# Edge Cases — Stories 3.7 e 3.11

## 3.7 Extratos Cliente

### EC-1: Filename nulo — `extratos_cliente.py:29`
`Path(file.filename).suffix.lower()` quebra se `filename=None`.
```python
def test_upload_filename_none(client, auth_headers):
    response = client.post("/api/v1/extratos/upload", files={"file": (None, b"data", "text/csv")}, headers=auth_headers)
    assert response.status_code == 422
```

### EC-2: Arquivo corrompido — `extratos_cliente.py:38-40`
Nenhuma validação do conteúdo — `.xlsx` com bytes inválidos é armazenado sem erro.
```python
def test_upload_corrupted_xlsx(client, auth_headers):
    garbage = b"PK\x03\x04" + b"\x00" * 100  # ZIP header inválido
    response = client.post("/api/v1/extratos/upload", files={"file": ("test.xlsx", garbage, "application/vnd.openxmlformats")}, headers=auth_headers)
    assert response.status_code in (400, 422)
```

### EC-3: Substring falso positivo — `extratos_cliente.py:106-114`
`"jan.xlsx" in "vendas_jan.xlsx"` → match incorreto durante validação.
```python
def test_validar_sem_falso_positivo(db, cliente_id):
    extrato = ExtratoCliente(nome_arquivo="report.csv", cliente_id=cliente_id)
    proc = Processamento(nome_arquivo="status_report.csv", cliente_id=cliente_id)
    db.add_all([extrato, proc]); db.commit()
    resultado = validar_extratos(db, cliente_id)
    assert extrato.status != "importado"  # não deve match
```

### EC-4: Path traversal — `extratos_cliente.py:158-160`
`caminho_arquivo` sem sanitização permite `../` escapar do diretório.
```python
def test_path_traversal_blocked(db, cliente_id):
    with pytest.raises(ValueError):
        salvar_extrato(db, cliente_id, caminho="../../../etc/passwd")
```

### EC-5: Race condition na exclusão — `extratos_cliente.py:194-195`
`exists()` + `unlink()` não são atômicos.
```python
def test_delete_concurrent(db, extrato_id):
    import threading
    erros = []
    def deletar():
        try: excluir_extrato(db, extrato_id)
        except Exception as e: erros.append(e)
    threads = [threading.Thread(target=deletar) for _ in range(2)]
    [t.start() for t in threads]; [t.join() for t in threads]
    assert len(erros) <= 1  # máximo 1 erro, não crash
```

### EC-6: Status nulo — `extratos_cliente.py:76-81`
Extrato com `status=None` não é contado em nenhuma categoria do resumo.
```python
def test_status_none_nao_quebra(db, cliente_id):
    extrato = ExtratoCliente(status=None, cliente_id=cliente_id)
    db.add(extrato); db.commit()
    resumo = status_resumo(db, cliente_id)
    assert resumo is not None  # não deve levantar exceção
```

### EC-7: Zero processamentos — `extratos_cliente.py:106-114`
Sem processamentos, todos extratos ficam "aguardando" sem indicação de problema.
```python
def test_validar_sem_processamentos(db, cliente_id):
    extrato = ExtratoCliente(nome_arquivo="jan.xlsx", cliente_id=cliente_id, status="aguardando")
    db.add(extrato); db.commit()
    resultado = validar_extratos(db, cliente_id)
    assert resultado["sem_processamentos"] is True  # deve sinalizar
```

---

## 3.11 Taxas Contratadas vs Cobradas

### EC-1: Taxa contratada negativa — `taxa_contratada_service.py:75`
`contratada > 0` protege divisão por zero, mas `contratada=-2.5` gera desvio errado.
```python
def test_taxa_contratada_negativa(db, processamento_id):
    taxa = TaxaContratada(taxa_contratada=-2.5, bandeira="Visa", modalidade="Crédito")
    db.add(taxa); db.commit()
    result = comparar_contratado_vs_cobrado(db, processamento_id)
    for item in result:
        assert item.desvio_percentual >= 0  # desvio nunca negativo
```

### EC-2: Todos tx_venda nulos — `taxa_contratada_service.py:54-56`
`taxa_media=0` quando todos NULL → desvio=100% → falso positivo de abusividade.
```python
def test_tx_venda_todos_nulos(db, processamento_id):
    # vendas com tx_venda=NULL
    result = comparar_contratado_vs_cobrado(db, processamento_id)
    for item in result:
        assert item.taxa_media is None or item.desvio_percentual == 0
```

### EC-3: Sem TaxaContratada configurada — `taxa_contratada_service.py:71-72`
Bandeira sem taxa configurada é silenciosamente ignorada.
```python
def test_bandeira_sem_taxa_configurada(db, processamento_id):
    result = comparar_contratado_vs_cobrado(db, processamento_id)
    bandeiras_sem_config = [r for r in result if r.sem_configuracao]
    assert len(bandeiras_sem_config) >= 0  # deve retornar campo, não omitir
```

### EC-4: Excesso negativo — `taxa_contratada_service.py:76`
`desvio < 0` gera `excesso` negativo (taxa cobrada menor que contratada).
```python
def test_excesso_nunca_negativo(db, processamento_id):
    result = comparar_contratado_vs_cobrado(db, processamento_id)
    for item in result:
        assert item.excesso_cobrado >= 0
```

### EC-5: Processamento sem vendas — `taxa_contratada_service.py:50-52`
```python
def test_processamento_sem_vendas(db):
    proc = Processamento(nome_arquivo="vazio.xlsx")
    db.add(proc); db.commit()
    result = comparar_contratado_vs_cobrado(db, proc.id)
    assert result == []  # lista vazia, não erro
```

### EC-6: Timezone mismatch — `taxa_contratada_service.py:33,65-67`
`proc.data_inicio` timezone-aware comparado com `vigencia_inicio` naive → off-by-one.
```python
def test_vigencia_timezone_naive_vs_aware(db):
    from datetime import datetime, timezone
    proc = Processamento(data_inicio=datetime(2026, 1, 15, tzinfo=timezone.utc))
    taxa = TaxaContratada(vigencia_inicio=date(2026, 1, 15), vigencia_fim=date(2026, 12, 31))
    # não deve levantar TypeError
    result = comparar_contratado_vs_cobrado(db, proc.id)
    assert result is not None
```

### EC-7: COUNT com tx_venda nulo — `taxa_contratada_service.py:40-42`
`COUNT(*)` conta linhas com `tx_venda=NULL`, mas `AVG()` as exclui → quantidade inflada.
```python
def test_quantidade_exclui_nulos(db, processamento_id):
    result = comparar_contratado_vs_cobrado(db, processamento_id)
    for item in result:
        # quantidade deve refletir apenas registros com tx_venda não nulo
        assert item.quantidade_transacoes == item.quantidade_com_taxa
```

---

## Severidade

| Edge Case | Story | Severidade | Risco |
|-----------|-------|-----------|-------|
| Path traversal | 3.7 | CRÍTICA | Segurança — acesso a arquivos do sistema |
| Falso positivo substring | 3.7 | ALTA | Dados — extratos marcados incorretamente |
| Taxa negativa → desvio errado | 3.11 | ALTA | Financeiro — relatório de abusividade incorreto |
| tx_venda NULL → desvio 100% | 3.11 | ALTA | Financeiro — falso alarme de abusividade |
| Race condition exclusão | 3.7 | MÉDIA | Estabilidade |
| Excesso negativo | 3.11 | MÉDIA | Dados financeiros incorretos |
| Timezone mismatch | 3.11 | MÉDIA | Erro silencioso em datas de vigência |
