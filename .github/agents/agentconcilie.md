# AGENTCONCILIE.md — Guia IA Completo para Financial Checker e Stack Moderno

---

## 1. Overview: Legado e Futuro

O **Financial Checker v2.0** é uma solução robusta de conciliação financeira (MySQL/SQLite), com pipeline de importação, análise, agregação, cálculo e reporting, preparada para ambientes de alta escala e portabilidade. Este documento unifica:
- Descrição funcional
- Fluxos técnicos
- Práticas de desenvolvimento e testes
- Problemas históricos e lições aprendidas
- Regras para agentes IA e contribuintes
- Plano e padrões para migração ao stack web moderno (Next.js + FastAPI)

>  **Meta**: Este markdown é a base viva de inteligência coletiva do projeto e da automação IA — deve ser retroalimentado a cada ciclo de evolução.

---

## 2. Arquitetura Atual — Legado Python
### **Diretórios & Componentes**
- `main.py`: Painel/tela principal, serve UI Panel + integra processamento.
- `modules/`: Views e controle UI (importação, gestão, analista, cálculos, gráficos, relatórios)
- `proc/`: ETL, normalização, bulk insert, classificação, lógica de usuários
- `conf/`: Autenticação, helpers (abstrações SQL camada dual MySQL/SQLite), settings globais
- `relatorios/`: Templates de relatórios
- `dev_tools/`: Scripts CLI para migração, debug, limpeza, análise

### **Banco de Dados**
- MySQL: produção/multiusuário; SQLite: client-side/distribuição
- Tabelas de vendas, recebíveis, análises, controles, logs, clientes, ECs, taxas, users, contextos, de-para
- DECIMAL(18,2) obrigatório para monetários; bulk insert sempre com dtype
- Migração/compatibilidade SQL dual via helpers

---

## 3. Fluxograma e Pipelines Técnicos (Importação→Cálculo→Reporting)

### **Fluxo Principal**
1. **Upload/importação**: Arquivos (.csv/.xls/.xlsx)→detect/cabeçalho→de-para mapeamento→normalização
2. **Classificação:** Filtros inteligentes (termos, status), separação processados/filtrados/diversos
3. **Gravação:** Bulk insert otimizado, dtype/DECIMAL em to_sql; processamentoID único e trackeável
4. **Cálculo:** Multi-layer (taxa específica→taxa genérica→fallback/min/log), agregações, relatórios
5. **Visual e Output:** UI Panel, gráficos Plotly, exportações PDF e dashboards
6. **Validação/Testes:** Automação post-install, checklist multi-modo, troubleshooting guiado e detalhado

### **Checklists Críticos**
- .round(2) aplicado em ETL/insere/antes de gravação
- dtype explícito em Pandas→to_sql
- Validação de consistência pós-importação (valores, log de erros)

---

## 4. Regras Absolutas para Todo Novo Código/Manutenção (AGENTE IA)
### **Sempre Fazer**
- Compatibilidade MySQL+SQLite sempre via helpers/adapters (ex.: _concat_sql, _date_format_sql, etc.)
- Usar DECIMAL(18,2) nas colunas monetárias, nunca DOUBLE/FLOAT/não tipado
- Atualizar sempre este markdown em qualquer refino estrutural/técnico
- Docstring obrigatória em toda função não-trivial
- Teste (manual e, se possível, automatizado) multi-banco
- Movimentar scripts utilitários/experimentos para dev_tools/ ou /scripts

### **Nunca Fazer**
- Assumir SQL puro de apenas um banco
- Cometer DOUBLE/FLOAT para dinheiro (leva a bugs graves!)
- Deixar documentação espalhada ou desatualizada
- Bulk insert sem especificar dtype

### **Arm. comuns a evitar**
- Deixar sem .round(2) após conversões monetárias
- Usar placeholders errados (ex.: %s sem adaptar para :param no SQLite)
- Falhar em inicializar variáveis antes de uso em queries dinâmicas

### **Checklist Padrão de Nova Feature**
- [ ] Dual-path testada (MySQL/SQLite)
- [ ] Docstring/PT-BR
- [ ] decimal/dtype nos inserts
- [ ] Teste manual funcional/ETL completo
- [ ] Documentação / este arquivo atualizado
- [ ] UI cobre cenário (Panel)

---

## 5. Testes, Validação e Troubleshooting ("GUIA_VALIDACAO_TESTES.md" Unificado)

- Modos de execução/teste: SQLite (single user) e MySQL (multiuser)
- Scripts validados em ambientes puros, VM, Sandbox
- Instalação (Poetry), smoke-test (`test_installation.bat`), pós-importação, alternância bancos
- Checklist básico: imports, versões, painel ativo, acesso admin, funções críticas (import, cálculo, relatório)
- Troubleshooting: erros comuns, python/poetry ausente, porta em uso, falha de bulk insert, bugs de arredondamento
- Scripts automação: garantindo setup verde antes de subir/dar manutenção

---

## 6. Diagnóstico Técnico e Lições de Projeto (Análise Crítica)
- Códigos SQL duplicados para MySQL e SQLite devem ser eliminados via abstração
- Atenção a tipos: DECIMAL sempre para dinheiro, VARCHAR para campos indexáveis
- Consistência de queries: usar sempre helpers, nunca string SQL "pura" para funcionalidades
- Todos os pontos fortes, riscos e métricas históricas em documentação (ver analisedeprojeto_completa.md)
- Logs e controles: logging de bugs críticos, automação de checagens e recálculo

---

## 7. AGENTE IA: Premissas e Diretrizes Herméticas
- Todas novas funções para banco/ETL/cálculo devem prever via helper SQL adapter
- Qualquer bug, aprendizado, workaround post-mortem → atualizar este markdown
- Lista viva de boas práticas, erros históricos e workflows:
    - .round(2) sempre!
    - dtype DECIMAL obrigatório
    - placeholders SQL adaptativos
    - separação clara de UI, core, banco e settings
- Sempre sugerir *docstring clara*, *exemplo de uso* e atualizar README/agent.

---

## 8. **Stack Moderno: Next.js + TypeScript + FastAPI + Poetry + pnpm**

### **8.1. Gerenciamento de Dependências**

#### **Poetry (Backend Python)**
```bash
# Instalação
curl -sSL https://install.python-poetry.org | python3 -

# Inicializar projeto
poetry init

# Adicionar dependências
poetry add fastapi uvicorn sqlalchemy pandas pydantic-settings
poetry add --group dev pytest black ruff mypy

# Instalar dependências
poetry install

# Executar comandos
poetry run python main.py
poetry run pytest
```

**pyproject.toml exemplo:**
```toml
[tool.poetry]
name = "financial-checker-api"
version = "2.0.0"
description = "API FastAPI para Financial Checker"
authors = ["Seu Nome <email@exemplo.com>"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
sqlalchemy = "^2.0.25"
pandas = "^2.2.0"
pydantic = "^2.6.0"
pydantic-settings = "^2.1.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
black = "^24.1.0"
ruff = "^0.2.0"
mypy = "^1.8.0"

[tool.poetry.scripts]
dev = "uvicorn app.main:app --reload"
start = "uvicorn app.main:app --host 0.0.0.0 --port 8000"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

#### **pnpm (Frontend Node.js)**
```bash
# Instalação
npm install -g pnpm

# Inicializar projeto
pnpm init

# Adicionar dependências
pnpm add next react react-dom
pnpm add -D typescript @types/react @types/node eslint prettier

# Instalar dependências
pnpm install

# Scripts
pnpm dev
pnpm build
pnpm start
```

**package.json exemplo:**
```json
{
  "name": "financial-checker-web",
  "version": "2.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "^14.1.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.7"
  },
  "devDependencies": {
    "@types/node": "^20.11.16",
    "@types/react": "^18.2.52",
    "@types/react-dom": "^18.2.18",
    "typescript": "^5.3.3",
    "eslint": "^8.56.0",
    "eslint-config-next": "^14.1.0",
    "prettier": "^3.2.4"
  }
}
```

---

### **8.2. Backend FastAPI Modularizado**

**Estrutura de Diretórios:**
```
apps/api/
├─ app/
│  ├─ __init__.py
│  ├─ main.py                 # Entry point FastAPI
│  ├─ config/
│  │  ├─ __init__.py
│  │  ├─ settings.py          # Configurações com pydantic-settings
│  │  └─ database.py          # Conexão DB
│  ├─ models/                 # SQLAlchemy models
│  │  ├─ __init__.py
│  │  ├─ vendas.py
│  │  ├─ recebiveis.py
│  │  └─ usuarios.py
│  ├─ schemas/                # Pydantic schemas (DTOs)
│  │  ├─ __init__.py
│  │  ├─ vendas.py
│  │  ├─ recebiveis.py
│  │  └─ auth.py
│  ├─ api/                    # Rotas/endpoints
│  │  ├─ __init__.py
│  │  ├─ deps.py              # Dependências compartilhadas
│  │  └─ v1/
│  │     ├─ __init__.py
│  │     ├─ api.py            # Router principal v1
│  │     └─ endpoints/
│  │        ├─ vendas.py
│  │        ├─ recebiveis.py
│  │        ├─ calculos.py
│  │        └─ auth.py
│  ├─ services/               # Lógica de negócio
│  │  ├─ __init__.py
│  │  ├─ vendas_service.py
│  │  ├─ calculos_service.py
│  │  └─ etl_service.py
│  ├─ repositories/           # Acesso a dados (Repository pattern)
│  │  ├─ __init__.py
│  │  ├─ base.py
│  │  ├─ vendas_repository.py
│  │  └─ recebiveis_repository.py
│  └─ utils/
│     ├─ __init__.py
│     ├─ sql_adapters.py      # Adaptadores MySQL/SQLite
│     ├─ validators.py
│     └─ formatters.py
├─ tests/
│  ├─ __init__.py
│  ├─ conftest.py
│  ├─ test_vendas.py
│  └─ test_calculos.py
├─ alembic/                   # Migrações DB
├─ pyproject.toml
├─ poetry.lock
└─ README.md
```

**app/main.py:**
```python
"""
Entry point da aplicação FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.api.v1.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
```

**app/config/settings.py:**
```python
"""
Configurações da aplicação usando Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Financial Checker API"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str
    DB_TYPE: str = "mysql"  # mysql ou sqlite
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

**app/api/v1/endpoints/vendas.py:**
```python
"""
Endpoints de vendas
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.vendas import VendaCreate, VendaResponse
from app.services.vendas_service import VendasService

router = APIRouter()

@router.post("/", response_model=VendaResponse, status_code=201)
async def criar_venda(
    venda: VendaCreate,
    db: Session = Depends(get_db)
):
    """
    Criar nova venda
    """
    service = VendasService(db)
    return await service.criar_venda(venda)

@router.get("/{venda_id}", response_model=VendaResponse)
async def obter_venda(
    venda_id: int,
    db: Session = Depends(get_db)
):
    """
    Obter venda por ID
    """
    service = VendasService(db)
    venda = await service.obter_venda(venda_id)
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    return venda
```

**app/services/vendas_service.py:**
```python
"""
Serviço de vendas - lógica de negócio
"""
from sqlalchemy.orm import Session
from app.repositories.vendas_repository import VendasRepository
from app.schemas.vendas import VendaCreate
from decimal import Decimal

class VendasService:
    def __init__(self, db: Session):
        self.repository = VendasRepository(db)
    
    async def criar_venda(self, venda: VendaCreate):
        """
        Criar venda com validações e normalizações
        """
        # Normalizar valor (sempre DECIMAL com .round(2))
        venda.valor = Decimal(str(venda.valor)).quantize(Decimal('0.01'))
        
        # Validar dados
        if venda.valor <= 0:
            raise ValueError("Valor deve ser positivo")
        
        # Criar no repositório
        return await self.repository.create(venda)
```

**app/repositories/base.py:**
```python
"""
Repository base com operações CRUD genéricas
"""
from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    async def get(self, id: int) -> Optional[ModelType]:
        """Buscar por ID"""
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Listar todos com paginação"""
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    async def create(self, obj_in: dict) -> ModelType:
        """Criar novo registro"""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    async def update(self, id: int, obj_in: dict) -> Optional[ModelType]:
        """Atualizar registro"""
        db_obj = await self.get(id)
        if db_obj:
            for field, value in obj_in.items():
                setattr(db_obj, field, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj
    
    async def delete(self, id: int) -> bool:
        """Deletar registro"""
        db_obj = await self.get(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False
```

**app/repositories/vendas_repository.py:**
```python
"""
Repository de vendas
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
from app.repositories.base import BaseRepository
from app.models.vendas import Venda

class VendasRepository(BaseRepository[Venda]):
    def __init__(self, db: Session):
        super().__init__(Venda, db)
    
    async def get_by_periodo(
        self, 
        data_inicio: datetime, 
        data_fim: datetime
    ) -> List[Venda]:
        """Buscar vendas por período"""
        return self.db.query(Venda).filter(
            and_(
                Venda.data >= data_inicio,
                Venda.data <= data_fim
            )
        ).all()
    
    async def get_by_status(self, status: str) -> List[Venda]:
        """Buscar vendas por status"""
        return self.db.query(Venda).filter(Venda.status == status).all()
    
    async def calcular_total_periodo(
        self, 
        data_inicio: datetime, 
        data_fim: datetime
    ) -> float:
        """Calcular total de vendas no período"""
        from sqlalchemy import func
        result = self.db.query(
            func.sum(Venda.valor_venda)
        ).filter(
            and_(
                Venda.data >= data_inicio,
                Venda.data <= data_fim
            )
        ).scalar()
        return float(result) if result else 0.0
```

**app/models/vendas.py:**
```python
"""
Model SQLAlchemy de vendas
"""
from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime

class Venda(Base):
    __tablename__ = "vendas_processadas"
    
    id = Column(Integer, primary_key=True, index=True)
    data = Column(DateTime, nullable=False, index=True)
    valor_venda = Column(DECIMAL(18, 2), nullable=False)
    valor_liquido = Column(DECIMAL(18, 2))
    status = Column(String(50), index=True)
    tipo_transacao = Column(String(100))
    bandeira = Column(String(50))
    autorizacao = Column(String(100))
    nsu = Column(String(100), unique=True)
    
    # Relacionamentos
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    cliente = relationship("Cliente", back_populates="vendas")
    
    processamento_id = Column(Integer, ForeignKey("processamentos.id"))
    processamento = relationship("Processamento", back_populates="vendas")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Venda(id={self.id}, data={self.data}, valor={self.valor_venda})>"
```

**app/models/base.py:**
```python
"""
Base model para SQLAlchemy
"""
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
```

**app/schemas/vendas.py:**
```python
"""
Pydantic schemas para vendas
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
from typing import Optional

class VendaBase(BaseModel):
    """Schema base de venda"""
    data: datetime
    valor_venda: Decimal = Field(..., decimal_places=2)
    tipo_transacao: Optional[str] = None
    bandeira: Optional[str] = None
    status: str = "processado"

class VendaCreate(VendaBase):
    """Schema para criação de venda"""
    cliente_id: int
    
    @validator('valor_venda')
    def validar_valor(cls, v):
        """Garantir valor positivo e arredondado"""
        if v <= 0:
            raise ValueError('Valor deve ser positivo')
        return Decimal(str(v)).quantize(Decimal('0.01'))

class VendaUpdate(BaseModel):
    """Schema para atualização de venda"""
    valor_venda: Optional[Decimal] = None
    status: Optional[str] = None
    valor_liquido: Optional[Decimal] = None
    
    @validator('valor_venda', 'valor_liquido')
    def validar_valores(cls, v):
        """Arredondar valores decimais"""
        if v is not None:
            return Decimal(str(v)).quantize(Decimal('0.01'))
        return v

class VendaResponse(VendaBase):
    """Schema de resposta de venda"""
    id: int
    valor_liquido: Optional[Decimal] = None
    nsu: Optional[str] = None
    autorizacao: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Para compatibilidade com SQLAlchemy
```

**app/config/database.py:**
```python
"""
Configuração de conexão com banco de dados
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config.settings import settings
from app.models.base import Base
from typing import Generator

# Criar engine com configurações apropriadas
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DB_ECHO if hasattr(settings, 'DB_ECHO') else False,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obter sessão do banco
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Criar todas as tabelas
    """
    Base.metadata.create_all(bind=engine)
```

**app/api/deps.py:**
```python
"""
Dependências compartilhadas para endpoints
"""
from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from app.config.database import get_db
from app.config.settings import settings
from app.models.usuarios import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Usuario:
    """
    Obter usuário autenticado do token JWT
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """
    Verificar se usuário está ativo
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo"
        )
    return current_user
```

**app/api/v1/api.py:**
```python
"""
Router principal da API v1
"""
from fastapi import APIRouter
from app.api.v1.endpoints import vendas, recebiveis, calculos, auth

api_router = APIRouter()

# Incluir todos os routers
api_router.include_router(
    auth.router, 
    prefix="/auth", 
    tags=["autenticação"]
)
api_router.include_router(
    vendas.router, 
    prefix="/vendas", 
    tags=["vendas"]
)
api_router.include_router(
    recebiveis.router, 
    prefix="/recebiveis", 
    tags=["recebíveis"]
)
api_router.include_router(
    calculos.router, 
    prefix="/calculos", 
    tags=["cálculos"]
)
```

**app/utils/sql_adapters.py:**
```python
"""
Adaptadores SQL para compatibilidade MySQL/SQLite
"""
from sqlalchemy import engine

def _is_sqlite(eng) -> bool:
    """Verificar se é SQLite"""
    return 'sqlite' in str(eng.url)

def _is_mysql(eng) -> bool:
    """Verificar se é MySQL"""
    return 'mysql' in str(eng.url)

def _concat_sql(eng, *args) -> str:
    """
    Concatenação de strings SQL compatível
    """
    if _is_sqlite(eng):
        return ' || '.join(args)
    return f"CONCAT({', '.join(args)})"

def _date_format_sql(eng, date_column: str, format_str: str) -> str:
    """
    Formatação de data SQL compatível
    """
    if _is_sqlite(eng):
        # SQLite usa strftime
        return f"strftime('{format_str}', {date_column})"
    # MySQL usa DATE_FORMAT
    return f"DATE_FORMAT({date_column}, '{format_str}')"

def _substring_sql(eng, column: str, start: int, length: int) -> str:
    """
    Substring SQL compatível
    """
    if _is_sqlite(eng):
        return f"SUBSTR({column}, {start}, {length})"
    return f"SUBSTRING({column}, {start}, {length})"

def _current_timestamp_sql(eng) -> str:
    """
    Timestamp atual SQL compatível
    """
    if _is_sqlite(eng):
        return "CURRENT_TIMESTAMP"
    return "NOW()"

def get_placeholder(eng, index: int = 1) -> str:
    """
    Retornar placeholder correto para o banco
    MySQL: %s
    SQLite: ?
    """
    if _is_sqlite(eng):
        return "?"
    return "%s"
```

---

### **8.3. Frontend Next.js + TypeScript Modularizado**

**Estrutura de Diretórios:**
```
apps/web/
├─ app/                       # App Router (Next.js 13+)
│  ├─ layout.tsx
│  ├─ page.tsx
│  ├─ (auth)/
│  │  ├─ login/
│  │  │  └─ page.tsx
│  │  └─ layout.tsx
│  ├─ (dashboard)/
│  │  ├─ vendas/
│  │  │  ├─ page.tsx
│  │  │  └─ [id]/
│  │  │     └─ page.tsx
│  │  ├─ recebiveis/
│  │  │  └─ page.tsx
│  │  ├─ calculos/
│  │  │  └─ page.tsx
│  │  └─ layout.tsx
│  └─ api/                    # API Routes (opcional)
│     └─ health/
│        └─ route.ts
├─ components/
│  ├─ ui/                     # Componentes base
│  │  ├─ Button.tsx
│  │  ├─ Input.tsx
│  │  ├─ Table.tsx
│  │  └─ Card.tsx
│  ├─ layout/                 # Layout components
│  │  ├─ Header.tsx
│  │  ├─ Sidebar.tsx
│  │  └─ Footer.tsx
│  ├─ vendas/                 # Componentes de vendas
│  │  ├─ VendasTable.tsx
│  │  ├─ VendaForm.tsx
│  │  └─ VendaCard.tsx
│  └─ shared/                 # Componentes compartilhados
│     ├─ Loading.tsx
│     └─ ErrorBoundary.tsx
├─ lib/
│  ├─ api/                    # Cliente API
│  │  ├─ client.ts
│  │  ├─ vendas.ts
│  │  ├─ recebiveis.ts
│  │  └─ auth.ts
│  ├─ hooks/                  # Custom hooks
│  │  ├─ useVendas.ts
│  │  ├─ useAuth.ts
│  │  └─ useDebounce.ts
│  ├─ utils/
│  │  ├─ formatters.ts
│  │  ├─ validators.ts
│  │  └─ constants.ts
│  └─ types/                  # TypeScript types
│     ├─ vendas.ts
│     ├─ recebiveis.ts
│     └─ api.ts
├─ public/
├─ styles/
│  └─ globals.css
├─ package.json
├─ tsconfig.json
├─ next.config.js
└─ .env.local
```

**lib/api/client.ts:**
```typescript
/**
 * Cliente API base
 */
import axios, { AxiosInstance } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor para tratar erros
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirecionar para login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

**lib/api/vendas.ts:**
```typescript
/**
 * API de vendas
 */
import { apiClient } from './client';
import { Venda, VendaCreate } from '@/lib/types/vendas';

export const vendasApi = {
  async listar(): Promise<Venda[]> {
    const { data } = await apiClient.get<Venda[]>('/vendas');
    return data;
  },

  async obter(id: number): Promise<Venda> {
    const { data } = await apiClient.get<Venda>(`/vendas/${id}`);
    return data;
  },

  async criar(venda: VendaCreate): Promise<Venda> {
    const { data } = await apiClient.post<Venda>('/vendas', venda);
    return data;
  },

  async atualizar(id: number, venda: Partial<Venda>): Promise<Venda> {
    const { data } = await apiClient.put<Venda>(`/vendas/${id}`, venda);
    return data;
  },

  async deletar(id: number): Promise<void> {
    await apiClient.delete(`/vendas/${id}`);
  },
};
```

**lib/hooks/useVendas.ts:**
```typescript
/**
 * Hook para gerenciar vendas
 */
import { useState, useEffect } from 'react';
import { vendasApi } from '@/lib/api/vendas';
import { Venda } from '@/lib/types/vendas';

export function useVendas() {
  const [vendas, setVendas] = useState<Venda[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchVendas = async () => {
    try {
      setLoading(true);
      const data = await vendasApi.listar();
      setVendas(data);
      setError(null);
    } catch (err) {
      setError('Erro ao carregar vendas');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVendas();
  }, []);

  return { vendas, loading, error, refetch: fetchVendas };
}
```

**components/vendas/VendasTable.tsx:**
```typescript
/**
 * Tabela de vendas
 */
'use client';

import { useVendas } from '@/lib/hooks/useVendas';
import { formatCurrency, formatDate } from '@/lib/utils/formatters';

export function VendasTable() {
  const { vendas, loading, error } = useVendas();

  if (loading) return <div>Carregando...</div>;
  if (error) return <div>Erro: {error}</div>;

  return (
    <table className="w-full">
      <thead>
        <tr>
          <th>ID</th>
          <th>Data</th>
          <th>Valor</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {vendas.map((venda) => (
          <tr key={venda.id}>
            <td>{venda.id}</td>
            <td>{formatDate(venda.data)}</td>
            <td>{formatCurrency(venda.valor)}</td>
            <td>{venda.status}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

---

### **8.4. Monorepo: Integração Completa**

**Estrutura Monorepo:**
```
financial-checker/
├─ apps/
│  ├─ web/                    # Next.js + TypeScript
│  │  ├─ package.json
│  │  └─ ...
│  └─ api/                    # FastAPI + Poetry
│     ├─ pyproject.toml
│     └─ ...
├─ packages/
│  ├─ shared-types/           # Types compartilhados
│  │  ├─ package.json
│  │  └─ index.ts
│  ├─ ui/                     # Component library
│  │  ├─ package.json
│  │  └─ components/
│  └─ config/                 # Configs compartilhadas
│     ├─ eslint-config/
│     └─ tsconfig/
├─ .github/
│  └─ workflows/
│     ├─ ci-web.yml
│     └─ ci-api.yml
├─ package.json               # Root package.json (pnpm workspace)
├─ pnpm-workspace.yaml
├─ turbo.json
└─ README.md
```

**pnpm-workspace.yaml:**
```yaml
packages:
  - 'apps/*'
  - 'packages/*'
```

**turbo.json:**
```json
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "dist/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "lint": {
      "dependsOn": ["^lint"]
    },
    "test": {
      "dependsOn": ["^build"]
    }
  }
}
```

**Root package.json:**
```json
{
  "name": "financial-checker-monorepo",
  "private": true,
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "lint": "turbo run lint",
    "test": "turbo run test",
    "web:dev": "pnpm --filter web dev",
    "api:dev": "cd apps/api && poetry run dev"
  },
  "devDependencies": {
    "turbo": "^1.11.0",
    "prettier": "^3.2.4"
  },
  "packageManager": "pnpm@8.15.0"
}
```

---

### **8.5. Referências e Recursos**

#### **Documentação Oficial**
- [Poetry Documentation](https://python-poetry.org/docs/)
- [pnpm Documentation](https://pnpm.io/)
- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [TurboRepo Documentation](https://turbo.build/repo/docs)

#### **Templates e Boilerplates**
- [Next.js FastAPI Template](https://nextfastapi.com/)
- [FastAPI Full Stack Template](https://github.com/tiangolo/full-stack-fastapi-template)
- [Next.js Boilerplate](https://github.com/vercel/next.js/tree/canary/examples)

#### **Ferramentas de Desenvolvimento**
- [openapi-typescript-codegen](https://github.com/ferdikoomen/openapi-typescript-codegen) - Gerar tipos TS do OpenAPI
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM Python
- [Alembic](https://alembic.sqlalchemy.org/) - Migrações de banco
- [Pytest](https://docs.pytest.org/) - Testes Python
- [Vitest](https://vitest.dev/) - Testes JavaScript/TypeScript

---

### **8.6. Melhores Práticas para o Agente IA**

#### **Backend (FastAPI + Poetry)**
- ✅ Sempre usar type hints em todas as funções
- ✅ Pydantic para validação de dados (schemas)
- ✅ Repository pattern para acesso a dados
- ✅ Service layer para lógica de negócio
- ✅ Async/await para operações I/O
- ✅ Testes com pytest e coverage > 80%
- ✅ DECIMAL(18,2) para valores monetários
- ✅ Docstrings em todas funções públicas

#### **Frontend (Next.js + TypeScript)**
- ✅ Componentes funcionais com TypeScript
- ✅ Custom hooks para lógica reutilizável
- ✅ Separação de concerns (UI/logic/data)
- ✅ Error boundaries para tratamento de erros
- ✅ Loading states em todas operações async
- ✅ Validação de formulários com Zod ou Yup
- ✅ Formatação consistente (Prettier + ESLint)
- ✅ Types gerados automaticamente do backend

#### **Integração**
- ✅ OpenAPI spec sempre atualizado
- ✅ CI/CD para ambos apps (web + api)
- ✅ Versionamento semântico
- ✅ Changelog mantido atualizado
- ✅ Environment variables com .env
- ✅ Docker compose para desenvolvimento local
- ✅ Documentação técnica atualizada
---

## 9. Apêndices: Snippets, Troubleshootings, Workflows, Casos de Uso

### **Exemplo Adaptador SQL Universal**
```python
def _concat_sql(engine, *args):
    if _is_sqlite(engine):
        return ' || '.join(args)
    return f"CONCAT({', '.join(args)})"
```

### **Bulk Insert Pandas to_sql (corrigir bug monetário)**
```python
from sqlalchemy.types import DECIMAL
df.to_sql(
    'vendas_processadas',
    con=engine,
    dtype={'Valor_da_venda': DECIMAL(18,2), ...},
    method='multi',
    if_exists='append',
    index=False
)
```

### **Checklist Pós-Deploy/Importação**
- [ ] Teste SQLite e MySQL ok?
- [ ] Tipagem dos dados monetários? Não há DOUBLE?
- [ ] Scripts & docs ok e versionados?
- [ ] Teste manual função crítica/processamento?
- [ ] AI/engine atualizado/escrito no agent.md?

---

**Este arquivo é ponto único de verdade e conhecimento. Toda contribuição IA ou humana deve passar por aquí. Ao migrar para Next.js/FastAPI, este agente será a fonte de onboarding de devs, aprendizado contínuo e prevenção de bugs herdados.**
