# =============================================================================
# IMPORTAÇÃO DAS BIBLIOTECAS NECESSÁRIAS
# =============================================================================
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from datetime import datetime
import os
import subprocess
import sys
import sqlite3

# Importações específicas para gerar PDF com a biblioteca ReportLab
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.colors import black

# =============================================================================
# CLASSE PRINCIPAL DA APLICAÇÃO
# =============================================================================
class AppCadastro(tk.Tk):
    def __init__(self):
        super().__init__()
        
        try:
            self.icon_img = tk.PhotoImage(file='logo.png')
            self.iconphoto(False, self.icon_img)
        except tk.TclError:
            print("Não foi possível carregar a logo como ícone.")

        self.db_conn = self.setup_database()
        self.title("Sistema de Cadastro de Alunos")
        self.state('zoomed') 
        self.apply_professional_theme()

        # --- MODIFICAÇÃO: ESTRUTURA PRINCIPAL RESPONSIVA ---
        # A janela principal agora tem sua coluna 0 configurada para expandir
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Permite que a lista de alunos expanda

        top_frame = ttk.Frame(self, style='Main.TFrame')
        top_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=5)
        top_frame.grid_columnconfigure(0, weight=1) # Permite que o container do formulário expanda

        bottom_frame = ttk.Frame(self, style='Main.TFrame')
        bottom_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)

        self.create_search_widgets(top_frame)

        main_form_frame = ttk.Frame(top_frame, style='Main.TFrame')
        main_form_frame.grid(row=1, column=0, sticky='ew', pady=(10,0))
        # Configuração de peso para as colunas do formulário
        main_form_frame.grid_columnconfigure(0, weight=1)
        main_form_frame.grid_columnconfigure(1, weight=1)
        
        self.widgets = {}
        self.create_form_widgets(main_form_frame)
        self.create_student_list_widgets(bottom_frame)
        
        self.limpar_campos()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        if hasattr(self, 'db_conn') and self.db_conn: self.db_conn.close()
        self.destroy()

    def setup_database(self):
        conn = sqlite3.connect('cadastros.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alunos (
                codigo INTEGER PRIMARY KEY, data_inscricao TEXT, area TEXT, nome_completo TEXT, 
                curso TEXT, sexo TEXT, data_nascimento TEXT, idade TEXT, cpf TEXT, estado_civil TEXT, 
                cep TEXT, rua TEXT, numero TEXT, complemento TEXT, ponto_referencia TEXT, contato1 TEXT, 
                contato2 TEXT, escola TEXT, frequenta_escola TEXT, serie TEXT, ensino TEXT, 
                trabalha TEXT, profissao TEXT, renda_mensal TEXT, nome_pai TEXT, nome_mae TEXT, 
                num_irmaos TEXT, pessoas_residencia TEXT, mora_pais TEXT, mora_mae_pai TEXT, 
                mora_parentes TEXT, mora_conjuge TEXT, nome_conjuge TEXT, renda_conjuge TEXT, 
                num_filhos TEXT, renda_familiar TEXT, beneficio_gov TEXT, qual_beneficio TEXT, 
                desc_familiar TEXT, data_inicio_curso TEXT, data_conclusao_curso TEXT, 
                desistencia TEXT, doc_id TEXT, doc_cpf TEXT, doc_residencia TEXT, doc_vacina TEXT, 
                doc_foto TEXT, observacao TEXT, aceite_declaracao TEXT
            )''')
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_cpf ON alunos (cpf)")
        except sqlite3.OperationalError: pass
        conn.commit()
        return conn

    def apply_professional_theme(self):
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        BG_COLOR, TEXT_COLOR, ACCENT_COLOR, BUTTON_TEXT_COLOR, BORDER_COLOR = "#F0F0F0", "#333333", "#0078D4", "#FFFFFF", "#CCCCCC"
        self.config(bg=BG_COLOR)
        self.style.configure('.', background=BG_COLOR, foreground=TEXT_COLOR)
        self.style.configure('Main.TFrame', background=BG_COLOR)
        self.style.configure('TLabel', background=BG_COLOR, foreground=TEXT_COLOR, font=('Helvetica', 9))
        self.style.configure('TLabelFrame', background=BG_COLOR, bordercolor=BORDER_COLOR)
        self.style.configure('TLabelFrame.Label', background=BG_COLOR, foreground=TEXT_COLOR, font=('Helvetica', 10, 'bold'))
        self.style.configure('TCheckbutton', background=BG_COLOR, foreground=TEXT_COLOR)
        self.style.map('TCheckbutton', background=[('active', BG_COLOR)])
        self.style.configure('TButton', background=ACCENT_COLOR, foreground=BUTTON_TEXT_COLOR, font=('Helvetica', 10, 'bold'), borderwidth=1)
        self.style.map('TButton', background=[('active', '#005a9e')])
        self.style.configure('TEntry', fieldbackground='#FFFFFF', foreground=TEXT_COLOR)
        self.style.configure('TCombobox', fieldbackground='#FFFFFF', foreground=TEXT_COLOR)
        self.style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))

    def carregar_ultimo_codigo(self):
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT MAX(codigo) FROM alunos")
            resultado = cursor.fetchone()[0]
            return resultado if resultado is not None else 0
        except Exception as e:
            print(f"Erro ao carregar último código: {e}"); return 0

    def calcular_idade(self, event=None):
        try:
            data_nasc = datetime.strptime(self.widgets['data_nascimento'].get(), '%d/%m/%Y')
            idade = datetime.today().year - data_nasc.year - ((datetime.today().month, datetime.today().day) < (data_nasc.month, data_nasc.day))
            self.widgets['idade'].config(state='normal'); self.widgets['idade'].delete(0, tk.END); self.widgets['idade'].insert(0, str(idade)); self.widgets['idade'].config(state='readonly')
        except ValueError:
            self.widgets['idade'].config(state='normal'); self.widgets['idade'].delete(0, tk.END); self.widgets['idade'].config(state='readonly')

    def create_search_widgets(self, parent):
        search_frame = ttk.LabelFrame(parent, text="Buscar Cadastro", padding="10")
        search_frame.grid(row=0, column=0, sticky='ew')
        ttk.Label(search_frame, text="Buscar por Código:").pack(side='left', padx=(0, 5))
        self.busca_codigo_entry = ttk.Entry(search_frame, width=15)
        self.busca_codigo_entry.pack(side='left', padx=5)
        ttk.Button(search_frame, text="Buscar", command=self.buscar_e_carregar_aluno).pack(side='left', padx=5)

    def create_student_list_widgets(self, parent):
        list_frame = ttk.LabelFrame(parent, text="Alunos Cadastrados (clique para carregar)", padding="10")
        list_frame.pack(fill="both", expand=True, padx=0, pady=5)
        columns = ('codigo', 'nome', 'cpf'); self.tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        self.tree.heading('codigo', text='Código'); self.tree.heading('nome', text='Nome Completo'); self.tree.heading('cpf', text='CPF')
        self.tree.column('codigo', width=80, anchor='center'); self.tree.column('nome', width=400); self.tree.column('cpf', width=150, anchor='center')
        tree_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        tree_scrollbar.pack(side='right', fill='y'); self.tree.pack(side='left', fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.carregar_aluno_da_lista)

    def create_form_widgets(self, parent):
        left_column = ttk.Frame(parent, style='Main.TFrame')
        left_column.grid(row=0, column=0, sticky='new', padx=(0, 10))
        
        right_column = ttk.Frame(parent, style='Main.TFrame')
        right_column.grid(row=0, column=1, sticky='new')

        # Permite que as colunas dentro dos frames se expandam
        left_column.grid_columnconfigure(0, weight=1)
        right_column.grid_columnconfigure(0, weight=1)

        combobox_options = {"area": ["Setor Cultural", "Setor Profissionalizante"], "curso": ["Violão", "Capoeira", "Corte e Costura", "Manicure", "Teatro", "Cabelereiro"], "sexo": ["Masculino", "Feminino", "Outros"], "estado_civil": ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"], "frequenta_escola": ["Sim", "Não"], "ensino": ["Infantil", "Fundamental", "Médio", "Profissional e Tecnológica", "Superior"], "trabalha": ["Sim", "Não"], "beneficio_gov": ["Sim", "Não"]}
        
        frame_configs = {
            "Ficha de Inscrição": [("Código:", "codigo", "entry", True, 10), ("Data da Inscrição:", "data_inscricao", "entry", True, 12), ("Área:", "area", "combo", False, 18),("Nome Completo:", "nome_completo", "entry", False, 35, 3), ("Curso:", "curso", "combo", False, 18), ("Sexo:", "sexo", "combo", False, 15), ("Data de Nascimento:", "data_nascimento", "entry", False, 18), ("Idade:", "idade", "entry", True, 10), ("CPF:", "cpf", "entry", False, 15), ("Estado Civil:", "estado_civil", "combo", False, 18), ("CEP:", "cep", "entry", False, 10), ("Rua:", "rua", "entry", False, 35, 3), ("N°:", "numero", "entry", False, 8), ("Complemento:", "complemento", "entry", False, 20, 3), ("Ponto de Referência:", "ponto_referencia", "entry", False, 35, 3), ("Contato 1:", "contato1", "entry", False, 15), ("Contato 2:", "contato2", "entry", False, 15)],
            "Dados da Residência": [("Nome do Pai:", "nome_pai", "entry", False, 40, 3), ("Nome da Mãe:", "nome_mae", "entry", False, 40, 3),("N° de irmãos:", "num_irmaos", "entry", False, 5), ("Pessoas na residência:", "pessoas_residencia", "entry", False, 5), ("Nome do Cônjuge:", "nome_conjuge", "entry", False, 40, 3), ("Renda do Cônjuge (R$):", "renda_conjuge", "entry", False, 15),("N° de filhos:", "num_filhos", "entry", False, 5), ("Renda Familiar (R$):", "renda_familiar", "entry", False, 15),("Recebe benefício?", "beneficio_gov", "combo", False, 8), ("Qual benefício?", "qual_beneficio", "entry", False, 40, 3)]
        }
        
        def create_fields(parent_frame, fields):
            # Configura as colunas do grid para serem responsivas
            parent_frame.grid_columnconfigure(1, weight=1)
            parent_frame.grid_columnconfigure(3, weight=1)
            parent_frame.grid_columnconfigure(5, weight=1)

            row, col = 0, 0
            for label, key, type, readonly, width, *span in fields:
                ttk.Label(parent_frame, text=label).grid(row=row, column=col, sticky="w", padx=5, pady=2)
                widget = ttk.Combobox(parent_frame, values=combobox_options.get(key, []), width=width) if type == "combo" else ttk.Entry(parent_frame, width=width)
                self.widgets[key] = widget
                colspan = span[0] if span else 1
                widget.grid(row=row, column=col + 1, sticky="we", padx=5, pady=2, columnspan=colspan)
                if readonly: widget.config(state="readonly")
                col += (1 + colspan)
                if col >= 6: col = 0; row += 1

        frame_ficha = ttk.LabelFrame(left_column, text="Ficha de Inscrição", padding="10")
        frame_ficha.grid(row=0, column=0, sticky='ew')
        create_fields(frame_ficha, frame_configs["Ficha de Inscrição"])
        self.widgets["data_nascimento"].bind("<FocusOut>", self.calcular_idade)

        frame_residencia = ttk.LabelFrame(left_column, text="Dados da Residência", padding="10")
        frame_residencia.grid(row=1, column=0, sticky='ew', pady=5)
        create_fields(frame_residencia, frame_configs["Dados da Residência"])
        
        frame_residencia.grid_columnconfigure(1, weight=1)
        check_fields = [("Mora só com os pais", "mora_pais"), ("Mora com mãe/pai", "mora_mae_pai"), ("Mora com parentes", "mora_parentes"), ("Mora com cônjuge", "mora_conjuge")]
        for i, (text, key) in enumerate(check_fields): 
            self.widgets[key] = tk.BooleanVar()
            ttk.Checkbutton(frame_residencia, text=text, variable=self.widgets[key]).grid(row=i + 5, column=0, columnspan=2, sticky='w', padx=5)
        
        ttk.Label(frame_residencia, text="Descrição Familiar:").grid(row=len(check_fields)+5, column=0, sticky="nw", padx=5, pady=2)
        self.widgets['desc_familiar'] = tk.Text(frame_residencia, height=3, width=80, bg="#FFFFFF", fg="#333333", relief="solid", borderwidth=1)
        self.widgets['desc_familiar'].grid(row=len(check_fields)+5, column=1, columnspan=5, sticky="we", padx=5, pady=2)

        frame_escolares = ttk.LabelFrame(right_column, text="Dados Escolares", padding="10")
        frame_escolares.grid(row=0, column=0, sticky='ew')
        frame_escolares.grid_columnconfigure(1, weight=1)
        frame_escolares.grid_columnconfigure(3, weight=1)
        
        ttk.Label(frame_escolares, text="Escola:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.widgets['escola'] = ttk.Entry(frame_escolares, width=50)
        self.widgets['escola'].grid(row=0, column=1, columnspan=3, sticky="we", padx=5, pady=2)
        ttk.Label(frame_escolares, text="Série:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.widgets['serie'] = ttk.Entry(frame_escolares, width=20)
        self.widgets['serie'].grid(row=1, column=1, sticky="we", padx=5, pady=2)
        ttk.Label(frame_escolares, text="Ensino:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        self.widgets['ensino'] = ttk.Combobox(frame_escolares, values=combobox_options.get('ensino', []), width=20)
        self.widgets['ensino'].grid(row=1, column=3, sticky="we", padx=5, pady=2)
        ttk.Label(frame_escolares, text="Profissão:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.widgets['profissao'] = ttk.Entry(frame_escolares, width=50)
        self.widgets['profissao'].grid(row=2, column=1, columnspan=3, sticky="we", padx=5, pady=2)
        ttk.Label(frame_escolares, text="Trabalha?:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.widgets['trabalha'] = ttk.Combobox(frame_escolares, values=combobox_options.get('trabalha', []), width=20)
        self.widgets['trabalha'].grid(row=3, column=1, sticky="we", padx=5, pady=2)
        ttk.Label(frame_escolares, text="Frequenta Escola?:").grid(row=3, column=2, sticky="w", padx=5, pady=2)
        self.widgets['frequenta_escola'] = ttk.Combobox(frame_escolares, values=combobox_options.get('frequenta_escola', []), width=20)
        self.widgets['frequenta_escola'].grid(row=3, column=3, sticky="we", padx=5, pady=2)
        ttk.Label(frame_escolares, text="Renda Mensal (R$):").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.widgets['renda_mensal'] = ttk.Entry(frame_escolares, width=20)
        self.widgets['renda_mensal'].grid(row=4, column=1, sticky="we", padx=5, pady=2)

        frame_curso = ttk.LabelFrame(right_column, text="Datas do Curso", padding="10")
        frame_curso.grid(row=1, column=0, sticky='ew', pady=5)
        
        doc_frame = ttk.LabelFrame(right_column, text="Documentos Entregues", padding="10"); doc_frame.grid(row=2, column=0, sticky='ew', pady=5)
        doc_fields = [("Identidade", "doc_id"), ("CPF", "doc_cpf"), ("Residência", "doc_residencia"), ("Vacina", "doc_vacina"), ("Foto 3x4", "doc_foto")]
        for i, (text, key) in enumerate(doc_fields): self.widgets[key] = tk.BooleanVar(); ttk.Checkbutton(doc_frame, text=text, variable=self.widgets[key]).pack(side='left', padx=10, expand=True)
        
        obs_frame = ttk.LabelFrame(right_column, text="Observação", padding="10"); obs_frame.grid(row=3, column=0, sticky='ew', pady=5)
        self.widgets['observacao'] = tk.Text(obs_frame, height=3, bg="#FFFFFF", fg="#333333", relief="solid", borderwidth=1); self.widgets['observacao'].pack(fill='x', expand=True, padx=5, pady=5)
        
        dec_frame = ttk.LabelFrame(right_column, text="Termo de Autorização", padding="10"); dec_frame.grid(row=4, column=0, sticky='ew', pady=5)
        self.widgets['aceite_declaracao'] = tk.BooleanVar(); ttk.Checkbutton(dec_frame, text="Autorizo o uso de imagem e voz para fins institucionais.", variable=self.widgets['aceite_declaracao']).pack(pady=5, anchor='w')
        
        btn_frame = ttk.Frame(right_column); btn_frame.grid(row=5, column=0, sticky='ew', pady=10)
        ttk.Button(btn_frame, text="Limpar", command=self.limpar_campos).pack(side='left', expand=True)
        ttk.Button(btn_frame, text="Gerar PDF", command=self.gerar_pdf).pack(side='right', expand=True, padx=5)
        ttk.Button(btn_frame, text="Salvar", command=self.salvar_cadastro).pack(side='right', expand=True)

    def coletar_dados(self):
        dados = {}
        for key, widget in self.widgets.items():
            try:
                if isinstance(widget, (ttk.Entry, ttk.Combobox)): dados[key] = widget.get().strip()
                elif isinstance(widget, tk.Text): dados[key] = widget.get("1.0", tk.END).strip()
                elif isinstance(widget, tk.BooleanVar): dados[key] = "Sim" if widget.get() else "Não"
            except: dados[key] = ""
        return dados

    def limpar_campos(self):
        codigo_atual = self.carregar_ultimo_codigo() + 1
        for key, widget in self.widgets.items():
            if key in ['codigo', 'data_inscricao']: continue
            if isinstance(widget, ttk.Combobox): widget.set('')
            elif isinstance(widget, ttk.Entry) and widget['state'] != 'readonly': widget.delete(0, tk.END)
            elif isinstance(widget, tk.Text): widget.delete("1.0", tk.END)
            elif isinstance(widget, tk.BooleanVar): widget.set(False)
        self.widgets['codigo'].config(state='normal'); self.widgets['codigo'].delete(0, tk.END); self.widgets['codigo'].insert(0, str(codigo_atual).zfill(4)); self.widgets['codigo'].config(state='readonly')
        self.widgets['data_inscricao'].config(state='normal'); self.widgets['data_inscricao'].delete(0, tk.END); self.widgets['data_inscricao'].insert(0, datetime.now().strftime('%d/%m/%Y')); self.widgets['data_inscricao'].config(state='readonly')
        self.widgets['idade'].config(state='normal'); self.widgets['idade'].delete(0, tk.END); self.widgets['idade'].config(state='readonly')
        self.busca_codigo_entry.delete(0, tk.END)
        if self.tree.selection(): self.tree.selection_remove(self.tree.selection())
        self.atualizar_lista_alunos()

    def salvar_cadastro(self):
        dados = self.coletar_dados(); cpf = dados.get('cpf'); codigo_atual = int(self.widgets['codigo'].get())
        if not dados.get('nome_completo') or not cpf or not dados.get('curso'):
            return messagebox.showerror("Erro de Validação", "Nome, CPF e Curso são campos obrigatórios!")
        cursor = self.db_conn.cursor(); cursor.execute("SELECT codigo FROM alunos WHERE cpf = ? AND codigo != ?", (cpf, codigo_atual))
        outro_aluno_com_cpf = cursor.fetchone()
        if outro_aluno_com_cpf: return messagebox.showerror("CPF Duplicado", f"O CPF '{cpf}' já está cadastrado para o aluno com código {outro_aluno_com_cpf[0]}.")
        colunas_ordem = ['codigo', 'data_inscricao', 'area', 'nome_completo', 'curso', 'sexo', 'data_nascimento', 'idade', 'cpf', 'estado_civil', 'cep', 'rua', 'numero', 'complemento', 'ponto_referencia', 'contato1', 'contato2', 'escola', 'frequenta_escola', 'serie', 'ensino', 'trabalha', 'profissao', 'renda_mensal', 'nome_pai', 'nome_mae', 'num_irmaos', 'pessoas_residencia','mora_pais', 'mora_mae_pai', 'mora_parentes', 'mora_conjuge', 'nome_conjuge', 'renda_conjuge', 'num_filhos', 'renda_familiar', 'beneficio_gov', 'qual_beneficio', 'desc_familiar','data_inicio_curso', 'data_conclusao_curso', 'desistencia', 'doc_id', 'doc_cpf', 'doc_residencia', 'doc_vacina', 'doc_foto', 'observacao', 'aceite_declaracao']
        dados['codigo'] = codigo_atual; valores = [dados.get(col, '') for col in colunas_ordem]
        try:
            placeholders = ', '.join(['?'] * len(valores))
            cursor.execute(f"INSERT OR REPLACE INTO alunos ({', '.join(colunas_ordem)}) VALUES ({placeholders})", valores)
            self.db_conn.commit(); messagebox.showinfo("Sucesso", f"Aluno {dados['nome_completo']} salvo com sucesso!"); self.limpar_campos()
        except Exception as e: messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar os dados no banco.\nErro: {e}")

    def buscar_e_carregar_aluno(self, codigo_busca=None):
        if codigo_busca is None:
            try: codigo_busca = int(self.busca_codigo_entry.get())
            except (ValueError, TypeError): return messagebox.showerror("Erro de Busca", "Por favor, digite um código de aluno válido.")
        cursor = self.db_conn.cursor(); cursor.execute("SELECT * FROM alunos WHERE codigo = ?", (codigo_busca,))
        aluno_encontrado = cursor.fetchone()
        if aluno_encontrado:
            nomes_colunas = [d[0] for d in cursor.description]; dados_aluno = dict(zip(nomes_colunas, aluno_encontrado))
            self.popular_formulario(dados_aluno)
        else: messagebox.showwarning("Não Encontrado", f"Nenhum aluno encontrado com o código {codigo_busca}.")

    def carregar_aluno_da_lista(self, event):
        selecao = self.tree.selection()
        if not selecao: return
        valores = self.tree.item(selecao[0], 'values'); self.buscar_e_carregar_aluno(int(valores[0]))

    def popular_formulario(self, dados_aluno):
        for key, widget in self.widgets.items():
            valor = dados_aluno.get(key, "")
            if isinstance(widget, ttk.Entry):
                is_readonly = widget['state'] == 'readonly'
                if is_readonly: widget.config(state='normal')
                widget.delete(0, tk.END); widget.insert(0, str(valor))
                if is_readonly: widget.config(state='readonly')
            elif isinstance(widget, ttk.Combobox): widget.set(str(valor))
            elif isinstance(widget, tk.Text): widget.delete("1.0", tk.END); widget.insert("1.0", str(valor))
            elif isinstance(widget, tk.BooleanVar): widget.set(True if valor == 'Sim' else False)

    def atualizar_lista_alunos(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        cursor = self.db_conn.cursor(); cursor.execute("SELECT codigo, nome_completo, cpf FROM alunos ORDER BY nome_completo ASC")
        for row in cursor.fetchall(): self.tree.insert("", "end", values=row)

    def gerar_pdf(self):
        dados = self.coletar_dados()
        if not dados.get('nome_completo'): return messagebox.showerror("Erro", "Carregue os dados de um aluno para gerar a ficha.")
        nome_aluno = dados.get('nome_completo', 'aluno_sem_nome'); codigo_aluno = dados.get('codigo', '0000')
        nome_arquivo = f"Ficha_Inscricao_{codigo_aluno}_{nome_aluno.replace(' ', '_')}.pdf"
        
        try:
            c = canvas.Canvas(nome_arquivo, pagesize=A4); largura, altura = A4
            
            MARGEM_X = 2*cm; MARGEM_Y_SUPERIOR = 27.5*cm; MARGEM_INFERIOR = 2.5*cm
            LARGURA_UTIL = largura - 2*MARGEM_X
            ESPACAMENTO_LINHA, ESPACAMENTO_SECAO = 0.6*cm, 1*cm
            y_atual = MARGEM_Y_SUPERIOR

            def check_page_break():
                nonlocal y_atual
                if y_atual < MARGEM_INFERIOR:
                    c.showPage(); y_atual = MARGEM_Y_SUPERIOR
                    return True
                return False

            def desenha_titulo_secao(texto):
                nonlocal y_atual
                if check_page_break(): y_atual -= 0.5*cm
                y_atual -= ESPACAMENTO_SECAO; c.setFont("Helvetica-Bold", 11); c.setFillColor(black)
                c.drawString(MARGEM_X, y_atual, texto.upper()); y_atual -= 0.1*cm
                c.line(MARGEM_X, y_atual, MARGEM_X + LARGURA_UTIL, y_atual); y_atual -= ESPACAMENTO_LINHA*1.5
            
            def desenha_campo(label, valor, x_offset: float = 0.0):
                nonlocal y_atual
                if check_page_break(): desenha_titulo_secao("Continuação da Ficha")
                c.setFont("Helvetica-Bold", 9); c.drawString(MARGEM_X + x_offset, y_atual, f"{label}:")
                c.setFont("Helvetica", 9); c.drawString(MARGEM_X + x_offset + 3.5*cm, y_atual, str(dados.get(valor, '')))

            def desenha_paragrafo(texto):
                nonlocal y_atual; check_page_break()
                p = Paragraph(texto, ParagraphStyle(name='Normal', fontName='Helvetica', fontSize=9, leading=12))
                largura_p, altura_p = p.wrapOn(c, LARGURA_UTIL, altura)
                if y_atual - altura_p < MARGEM_INFERIOR: c.showPage(); y_atual = MARGEM_Y_SUPERIOR; desenha_titulo_secao("Continuação da Ficha")
                y_atual -= altura_p; p.drawOn(c, MARGEM_X, y_atual); y_atual -= ESPACAMENTO_LINHA
            
            try: c.drawImage("logo.png", MARGEM_X, y_atual-1.2*cm, width=4*cm, height=2.5*cm, preserveAspectRatio=True, anchor='n')
            except: c.drawString(MARGEM_X, y_atual-0.5*cm, "[Logo]")
            c.setFont("Helvetica-Bold", 18); c.drawCentredString(largura/2, y_atual, "FICHA DE INSCRIÇÃO"); y_atual -= 0.5*cm
            c.line(MARGEM_X, y_atual, LARGURA_UTIL + MARGEM_X, y_atual)
            
            desenha_titulo_secao("Ficha de Inscrição")
            desenha_campo("Código", "codigo"); desenha_campo("Data da Inscrição", "data_inscricao", x_offset=8.5*cm); y_atual -= ESPACAMENTO_LINHA
            desenha_campo("Nome Completo", "nome_completo"); y_atual -= ESPACAMENTO_LINHA
            desenha_campo("Curso", "curso"); desenha_campo("Área", "area", x_offset=8.5*cm); y_atual -= ESPACAMENTO_LINHA
            desenha_campo("Data de Nascimento", "data_nascimento"); desenha_campo("Idade", "idade", x_offset=8.5*cm); y_atual -= ESPACAMENTO_LINHA
            desenha_campo("CPF", "cpf"); desenha_campo("Sexo", "sexo", x_offset=8.5*cm); y_atual -= ESPACAMENTO_LINHA
            desenha_campo("Estado Civil", "estado_civil")
            
            desenha_titulo_secao("Endereço e Contato")
            desenha_campo("CEP", "cep"); desenha_campo("Rua", "rua", x_offset=5*cm); y_atual -= ESPACAMENTO_LINHA
            desenha_campo("Número", "numero"); desenha_campo("Complemento", "complemento", x_offset=5*cm); y_atual -= ESPACAMENTO_LINHA
            desenha_campo("Ponto de Referência", "ponto_referencia"); y_atual -= ESPACAMENTO_LINHA
            desenha_campo("Contato 1", "contato1"); desenha_campo("Contato 2", "contato2", x_offset=8.5*cm)
            
            desenha_titulo_secao("Dados Escolares")
            desenha_campo("Escola", "escola"); desenha_campo("Frequenta?", "frequenta_escola", x_offset=10*cm); y_atual -= ESPACAMENTO_LINHA
            desenha_campo("Série", "serie"); desenha_campo("Ensino", "ensino", x_offset=8.5*cm); y_atual -= ESPACAMENTO_LINHA
            desenha_campo("Trabalha?", "trabalha"); desenha_campo("Profissão", "profissao", x_offset=8.5*cm); y_atual -= ESPACAMENTO_LINHA
            desenha_campo("Renda Mensal", "renda_mensal")

            desenha_titulo_secao("Dados da Residência")
            desenha_campo("Nome do Pai", "nome_pai"); y_atual -= ESPACAMENTO_LINHA
            desenha_campo("Nome da Mãe", "nome_mae"); y_atual -= ESPACAMENTO_LINHA
            desenha_campo("N° de Irmãos", "num_irmaos"); desenha_campo("Pessoas na Residência", "pessoas_residencia", x_offset=8.5*cm); y_atual -= ESPACAMENTO_LINHA
            desenha_campo("N° de Filhos", "num_filhos"); desenha_campo("Renda Familiar", "renda_familiar", x_offset=8.5*cm); y_atual -= ESPACAMENTO_LINHA
            desenha_campo("Nome do Cônjuge", "nome_conjuge"); desenha_campo("Renda do Cônjuge", "renda_conjuge", x_offset=8.5*cm); y_atual -= ESPACAMENTO_LINHA
            check_texto = f"Mora com: {'Pais' if dados.get('mora_pais')=='Sim' else ''} {'Mãe/Pai' if dados.get('mora_mae_pai')=='Sim' else ''} {'Parentes' if dados.get('mora_parentes')=='Sim' else ''} {'Cônjuge' if dados.get('mora_conjuge')=='Sim' else ''}"
            c.setFont("Helvetica-Bold", 9); c.drawString(MARGEM_X, y_atual, "Configuração de Moradia:"); c.setFont("Helvetica", 9); c.drawString(MARGEM_X + 4*cm, y_atual, check_texto)
            y_atual -= ESPACAMENTO_LINHA; desenha_campo("Recebe Benefício?", "beneficio_gov"); desenha_campo("Qual?", "qual_beneficio", x_offset=8.5*cm); y_atual -= ESPACAMENTO_LINHA
            c.setFont("Helvetica-Bold", 9); c.drawString(MARGEM_X, y_atual, "Descrição Familiar:"); y_atual -= 0.4*cm
            desenha_paragrafo(dados.get('desc_familiar', ''))

            desenha_titulo_secao("Documentos Entregues")
            doc_texto = f"ID: {'(X)' if dados.get('doc_id')=='Sim' else '( )'} | CPF: {'(X)' if dados.get('doc_cpf')=='Sim' else '( )'} | Residência: {'(X)' if dados.get('doc_residencia')=='Sim' else '( )'} | Vacina: {'(X)' if dados.get('doc_vacina')=='Sim' else '( )'} | Foto 3x4: {'(X)' if dados.get('doc_foto')=='Sim' else '( )'}"
            c.setFont("Helvetica", 9); c.drawString(MARGEM_X, y_atual, doc_texto)

            desenha_titulo_secao("Observações"); desenha_paragrafo(dados.get('observacao', 'Nenhuma observação.'))
            desenha_titulo_secao("Termo de Autorização de Imagem")
            desenha_paragrafo("Autorizo, de forma gratuita, a utilização da minha imagem e voz para fins de divulgação institucional, conforme Lei de Direitos Autorais (Lei nº 9.610/1998).")
            y_atual -= ESPACAMENTO_LINHA; c.setFont("Helvetica-Bold", 10); c.drawString(MARGEM_X, y_atual, f"[{'X' if dados.get('aceite_declaracao')=='Sim' else ' '}] LI E CONCORDO COM OS TERMOS")
            
            y_atual -= 3*cm; check_page_break()
            c.line(largura/2 - 6*cm, y_atual, largura/2 + 6*cm, y_atual)
            c.drawCentredString(largura/2, y_atual-0.4*cm, "Assinatura do Aluno ou Responsável")
            
            c.save()
            messagebox.showinfo("PDF Gerado", f"O PDF da ficha foi salvo como:\n'{nome_arquivo}'")
            if sys.platform == "win32": os.startfile(nome_arquivo)
            else: subprocess.call(["open" if sys.platform == "darwin" else "xdg-open", nome_arquivo])
        except Exception as e: messagebox.showerror("Erro ao Gerar PDF", f"Não foi possível criar o arquivo PDF.\nErro técnico: {e}")

if __name__ == "__main__":
    try:
        app = AppCadastro()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Erro Crítico", f"Ocorreu um erro fatal:\n\n{e}")