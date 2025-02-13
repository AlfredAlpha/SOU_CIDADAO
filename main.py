import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.core.window import Window
from plyer import filechooser, camera
from pathlib import Path

# Cores da bandeira de Cabreúva/SP (exemplo)
CORES = {
    "verde": "#008000",
    "branco": "#FFFFFF",
    "azul": "#0000FF"
}

# Vereadores pré-definidos
VEREADORES = [
    {"nome": "Vereador 1", "email": "vereador1@cabreuva.sp.gov.br"},
    {"nome": "Vereador 2", "email": "vereador2@cabreuva.sp.gov.br"}
]

# Configurações de e-mail
EMAIL_HOST = "smtp.gmail.com"  # Exemplo usando Gmail
EMAIL_PORT = 587
EMAIL_USER = "seu_email@gmail.com"
EMAIL_PASSWORD = "sua_senha"

class TelaApresentacao(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        layout.add_widget(Label(text="Sou Cidadão", font_size=40, color=CORES["azul"]))
        layout.add_widget(Label(text="Envie suas solicitações aos vereadores", font_size=20, color=CORES["verde"]))
        layout.add_widget(Button(text="Iniciar", on_press=self.ir_para_selecao, size_hint=(1, 0.2)))
        self.add_widget(layout)

    def ir_para_selecao(self, instance):
        self.manager.current = "selecao_vereador"

class TelaSelecaoVereador(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        layout.add_widget(Label(text="Selecione o Vereador", font_size=30, color=CORES["azul"]))
        for vereador in VEREADORES:
            btn = Button(text=vereador["nome"], on_press=self.selecionar_vereador, size_hint=(1, 0.2))
            btn.vereador = vereador
            layout.add_widget(btn)
        self.add_widget(layout)

    def selecionar_vereador(self, instance):
        self.manager.vereador_selecionado = instance.vereador
        self.manager.current = "preencher_dados"

class TelaPreencherDados(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        self.layout.add_widget(Label(text="Preencha os Dados", font_size=30, color=CORES["azul"]))
        self.nome = TextInput(hint_text="Nome", size_hint=(1, 0.2))
        self.telefone = TextInput(hint_text="Telefone", size_hint=(1, 0.2))
        self.descricao = TextInput(hint_text="Descrição", size_hint=(1, 0.4))
        self.layout.add_widget(self.nome)
        self.layout.add_widget(self.telefone)
        self.layout.add_widget(self.descricao)
        self.layout.add_widget(Button(text="Próximo", on_press=self.ir_para_foto, size_hint=(1, 0.2)))
        self.add_widget(self.layout)

    def ir_para_foto(self, instance):
        self.manager.dados_usuario = {
            "nome": self.nome.text,
            "telefone": self.telefone.text,
            "descricao": self.descricao.text
        }
        self.manager.current = "adicionar_foto"

class TelaAdicionarFoto(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        self.layout.add_widget(Label(text="Adicionar Foto", font_size=30, color=CORES["azul"]))
        self.foto_path = None
        self.layout.add_widget(Button(text="Tirar Foto", on_press=self.tirar_foto, size_hint=(1, 0.2)))
        self.layout.add_widget(Button(text="Escolher da Galeria", on_press=self.escolher_foto, size_hint=(1, 0.2)))
        self.layout.add_widget(Button(text="Próximo", on_press=self.ir_para_confirmacao, size_hint=(1, 0.2)))
        self.add_widget(self.layout)

    def tirar_foto(self, instance):
        try:
            camera.take_picture(filename="foto.jpg", on_complete=self.carregar_foto)
        except Exception as e:
            self.mostrar_erro(str(e))

    def escolher_foto(self, instance):
        try:
            filechooser.open_file(on_selection=self.carregar_foto)
        except Exception as e:
            self.mostrar_erro(str(e))

    def carregar_foto(self, caminho):
        if isinstance(caminho, list):
            caminho = caminho[0]
        self.foto_path = caminho
        self.mostrar_erro("Foto carregada com sucesso!")

    def mostrar_erro(self, mensagem):
        popup = Popup(title="Aviso", size_hint=(0.8, 0.4))
        popup.content = Label(text=mensagem)
        popup.open()

    def ir_para_confirmacao(self, instance):
        self.manager.foto_path = self.foto_path
        self.manager.current = "confirmacao"

class TelaConfirmacao(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        self.layout.add_widget(Label(text="Confirme os Dados", font_size=30, color=CORES["azul"]))
        self.dados_label = Label(text="", font_size=20, color=CORES["verde"])
        self.layout.add_widget(self.dados_label)
        self.layout.add_widget(Button(text="Enviar", on_press=self.enviar_email, size_hint=(1, 0.2)))
        self.layout.add_widget(Button(text="Voltar ao Início", on_press=self.voltar_inicio, size_hint=(1, 0.2)))
        self.add_widget(self.layout)

    def on_pre_enter(self, *args):
        dados = self.manager.dados_usuario
        vereador = self.manager.vereador_selecionado
        self.dados_label.text = f"Nome: {dados['nome']}\nTelefone: {dados['telefone']}\nDescrição: {dados['descricao']}\nVereador: {vereador['nome']}"

    def enviar_email(self, instance):
        try:
            # Configura o e-mail
            msg = MIMEMultipart()
            msg["From"] = EMAIL_USER
            msg["To"] = self.manager.vereador_selecionado["email"]
            msg["Subject"] = "Solicitação do Cidadão"
            corpo = f"Nome: {self.manager.dados_usuario['nome']}\nTelefone: {self.manager.dados_usuario['telefone']}\nDescrição: {self.manager.dados_usuario['descricao']}"
            msg.attach(MIMEText(corpo, "plain"))

            # Anexa a foto, se existir
            if self.manager.foto_path:
                with open(self.manager.foto_path, "rb") as f:
                    img = MIMEImage(f.read())
                    msg.attach(img)

            # Envia o e-mail
            with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
                server.starttls()
                server.login(EMAIL_USER, EMAIL_PASSWORD)
                server.send_message(msg)

            self.mostrar_erro("E-mail enviado com sucesso!")
        except Exception as e:
            self.mostrar_erro(f"Erro ao enviar e-mail: {str(e)}")

    def voltar_inicio(self, instance):
        self.manager.current = "apresentacao"

    def mostrar_erro(self, mensagem):
        popup = Popup(title="Aviso", size_hint=(0.8, 0.4))
        popup.content = Label(text=mensagem)
        popup.open()

class SouCidadaoApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(TelaApresentacao(name="apresentacao"))
        sm.add_widget(TelaSelecaoVereador(name="selecao_vereador"))
        sm.add_widget(TelaPreencherDados(name="preencher_dados"))
        sm.add_widget(TelaAdicionarFoto(name="adicionar_foto"))
        sm.add_widget(TelaConfirmacao(name="confirmacao"))
        return sm

if __name__ == "__main__":
    SouCidadaoApp().run()