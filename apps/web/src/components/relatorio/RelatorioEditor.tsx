'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useEditor, EditorContent, ReactRenderer } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Suggestion, { SuggestionOptions, SuggestionProps, SuggestionKeyDownProps } from '@tiptap/suggestion';
import { Extension, Editor, Range } from '@tiptap/core';
import tippy, { Instance as TippyInstance } from 'tippy.js';
import { RelatorioTag } from '@/lib/api/relatorio-tags';

// ---------------------------------------------------------------------------
// Slash Command List Component
// ---------------------------------------------------------------------------

interface SlashListProps {
  items: RelatorioTag[];
  command: (item: RelatorioTag) => void;
}

const SlashList = React.forwardRef<{ onKeyDown: (e: KeyboardEvent) => boolean }, SlashListProps>(
  ({ items, command }, ref) => {
    const [selectedIndex, setSelectedIndex] = useState(0);

    const selectItem = useCallback(
      (index: number) => {
        const item = items[index];
        if (item) command(item);
      },
      [items, command]
    );

    // Reset selection index when items list changes (legitimate pattern for suggestion menus)
    // eslint-disable-next-line react-hooks/set-state-in-effect
    useEffect(() => setSelectedIndex(0), [items]);

    React.useImperativeHandle(ref, () => ({
      onKeyDown: (e: KeyboardEvent) => {
        if (e.key === 'ArrowUp') {
          setSelectedIndex((prev) => (prev - 1 + items.length) % items.length);
          return true;
        }
        if (e.key === 'ArrowDown') {
          setSelectedIndex((prev) => (prev + 1) % items.length);
          return true;
        }
        if (e.key === 'Enter') {
          selectItem(selectedIndex);
          return true;
        }
        return false;
      },
    }));

    if (items.length === 0) {
      return (
        <div className="slash-menu bg-white border border-gray-200 rounded-lg shadow-lg p-2 text-sm text-gray-400">
          Nenhuma tag encontrada
        </div>
      );
    }

    return (
      <div className="slash-menu bg-white border border-gray-200 rounded-lg shadow-lg overflow-hidden max-h-64 overflow-y-auto w-64">
        {items.slice(0, 10).map((item, index) => (
          <button
            key={item.id}
            onClick={() => selectItem(index)}
            className={`w-full text-left px-3 py-2 text-sm hover:bg-primary/5 flex flex-col gap-0.5 ${
              index === selectedIndex ? 'bg-primary/10 text-primary' : 'text-gray-700'
            }`}
          >
            <span className="font-semibold">{item.nome}</span>
            {item.descricao && (
              <span className="text-xs text-gray-400 truncate">{item.descricao}</span>
            )}
          </button>
        ))}
      </div>
    );
  }
);
SlashList.displayName = 'SlashList';

// ---------------------------------------------------------------------------
// Slash Command Extension
// ---------------------------------------------------------------------------

function buildSlashExtension(tags: RelatorioTag[]): Extension {
  return Extension.create({
    name: 'slashCommand',
    addOptions() {
      return { suggestion: {} as SuggestionOptions };
    },
    addProseMirrorPlugins() {
      return [
        Suggestion({
          editor: this.editor,
          char: '/',
          startOfLine: false,
          items: ({ query }: { query: string }) => {
            const q = query.toLowerCase();
            return tags.filter(
              (t) =>
                t.ativo &&
                (t.nome.toLowerCase().includes(q) ||
                  (t.descricao ?? '').toLowerCase().includes(q))
            );
          },
          render: () => {
            let component: ReactRenderer<{ onKeyDown: (e: KeyboardEvent) => boolean }, SlashListProps>;
            let popup: TippyInstance[];

            return {
              onStart(props: SuggestionProps<RelatorioTag>) {
                component = new ReactRenderer(SlashList, {
                  props,
                  editor: props.editor,
                });
                popup = tippy('body', {
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  getReferenceClientRect: props.clientRect as any,
                  appendTo: () => document.body,
                  content: component.element,
                  showOnCreate: true,
                  interactive: true,
                  trigger: 'manual',
                  placement: 'bottom-start',
                });
              },
              onUpdate(props: SuggestionProps<RelatorioTag>) {
                component.updateProps(props);
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                popup[0].setProps({ getReferenceClientRect: props.clientRect as any });
              },
              onKeyDown(props: SuggestionKeyDownProps) {
                if (props.event.key === 'Escape') {
                  popup[0].hide();
                  return true;
                }
                return component.ref?.onKeyDown(props.event) ?? false;
              },
              onExit() {
                popup[0].destroy();
                component.destroy();
              },
            };
          },
          command: ({
            editor,
            range,
            props,
          }: {
            editor: Editor;
            range: Range;
            props: RelatorioTag;
          }) => {
            editor
              .chain()
              .focus()
              .deleteRange(range)
              .insertContent(props.conteudo_padrao)
              .run();
          },
        }),
      ];
    },
  });
}

// ---------------------------------------------------------------------------
// RelatorioEditor Component
// ---------------------------------------------------------------------------

interface RelatorioEditorProps {
  initialContent: string;
  tags?: RelatorioTag[];
  onChange?: (html: string) => void;
  onSave?: (html: string) => Promise<void>;
  saveLabel?: string;
}

export function RelatorioEditor({ initialContent, tags = [], onChange, onSave, saveLabel = 'Salvar' }: RelatorioEditorProps) {
  // Build extension once on mount; TipTap does not support runtime extension updates
  // without destroying/recreating the editor, so tags are captured at initialization.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const extensions = useMemo(() => [StarterKit, buildSlashExtension(tags)], []);

  const editor = useEditor({
    immediatelyRender: false,
    extensions,
    content: initialContent,
    onUpdate: ({ editor }) => {
      onChange?.(editor.getHTML());
    },
  });

  if (!editor) return null;

  return (
    <div className="relatorio-editor border border-gray-200 rounded-lg overflow-hidden">
      {/* Toolbar */}
      <div className="flex gap-1 p-2 border-b border-gray-100 bg-gray-50 flex-wrap">
        {[
          { label: 'B', action: () => editor.chain().focus().toggleBold().run(), active: editor.isActive('bold'), title: 'Negrito' },
          { label: 'I', action: () => editor.chain().focus().toggleItalic().run(), active: editor.isActive('italic'), title: 'Itálico' },
        ].map(({ label, action, active, title }) => (
          <button
            key={label}
            onClick={action}
            title={title}
            className={`px-2 py-1 text-sm rounded font-medium ${active ? 'bg-primary text-white' : 'hover:bg-gray-200 text-gray-700'}`}
          >
            {label}
          </button>
        ))}
        {[1, 2, 3].map((level) => (
          <button
            key={level}
            onClick={() => editor.chain().focus().toggleHeading({ level: level as 1 | 2 | 3 }).run()}
            title={`H${level}`}
            className={`px-2 py-1 text-xs rounded font-bold ${
              editor.isActive('heading', { level }) ? 'bg-primary text-white' : 'hover:bg-gray-200 text-gray-700'
            }`}
          >
            H{level}
          </button>
        ))}
        <button
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          title="Lista"
          className={`px-2 py-1 text-sm rounded ${editor.isActive('bulletList') ? 'bg-primary text-white' : 'hover:bg-gray-200 text-gray-700'}`}
        >
          ≡
        </button>
        <span className="ml-auto text-xs text-gray-400 flex items-center">
          Digite <kbd className="mx-1 px-1 bg-gray-200 rounded text-xs">/</kbd> para inserir tag
        </span>
        {onSave && (
          <button
            onClick={() => onSave(editor.getHTML())}
            className="ml-2 px-3 py-1 text-sm rounded bg-primary text-white hover:bg-primary/90"
          >
            {saveLabel}
          </button>
        )}
      </div>

      {/* Editor Area */}
      <EditorContent
        editor={editor}
        className="prose max-w-none p-4 min-h-[400px] focus:outline-none"
      />
    </div>
  );
}

export default RelatorioEditor;
