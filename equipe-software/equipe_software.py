import threading
from time import sleep

from maspy import *

_rm_de_mensagem = threading.local()


class Membro(Agent):
    def add(self, data_type, instant=False, no_lock=False):
        super().add(data_type, instant, no_lock)
        if isinstance(data_type, Plan):
            self._build_plan_index()

    def get(self, *args, **kwargs):
        if getattr(_rm_de_mensagem, "ativo", False):
            kwargs["no_lock"] = True
        return super().get(*args, **kwargs)

    def rm(self, data_type, instant=False, no_lock=False):
        if not no_lock:
            return super().rm(data_type, instant, no_lock)
        _rm_de_mensagem.ativo = True
        try:
            return super().rm(data_type, instant, no_lock)
        finally:
            _rm_de_mensagem.ativo = False


class Memoria(Membro):
    def __init__(self, agt_name=None):
        super().__init__(agt_name)
        self.add(Belief("convencao", "pytest + PEP 8 + docstrings"))

    @pl(gain, Belief("pendente", Any))
    def on_pendente(self, src, feature):
        self.print(f"pendencia '{feature}' registrada por {src}")

    @pl(gain, Belief("licao", Any))
    def on_licao(self, src, licao):
        self.print(f"memorizei licao de {src}: {licao}")

    @pl(gain, Belief("entrega", (Any, Any)))
    def on_entrega(self, src, args):
        self.print(f"registrada entrega: {args[0]} v{args[1]}")

    @pl(lose, Belief("pendente", Any))
    def on_pendente_removida(self, src, feature):
        self.print(f"pendencia '{feature}' removida (untell de {src})")

    @pl(gain, Belief("encerrar"))
    def encerrar(self, src):
        self.stop_cycle()


class Orquestrador(Membro):
    @pl(gain, Goal("entregar", (Any, Any)))
    def entregar(self, src, args):
        feature, descricao = args
        self.print(f"nova tarefa: {feature} ({descricao})")
        self.send("Memoria", tell, Belief("pendente", feature))
        self.send("Dev", achieve, Goal("implementar", (feature, descricao)))

    @pl(gain, Belief("codigo_pronto", (Any, Any, Any)))
    def codigo_pronto(self, src, codigo):
        self.print(f"{src} entregou {codigo[0]} v{codigo[1]}; mandando para o QA")
        self.send("QA", achieve, Goal("testar", codigo))

    @pl(gain, Belief("resultado_teste", (Any, Any, Any, Any)))
    def resultado(self, src, args):
        feature, versao, status, detalhe = args
        if status == "reprovado":
            self.print(f"v{versao} reprovada ({detalhe}); pedindo correcao ao Dev")
            self.send("Dev", achieve, Goal("corrigir", (feature, versao, detalhe)))
        else:
            self.print(f"v{versao} aprovada; encerrando a entrega de {feature}")
            self.send("Memoria", tell, Belief("entrega", (feature, versao)))
            self.send("Memoria", untell, Belief("pendente", feature))
            sleep(0.5)
            self.send(broadcast, tell, Belief("encerrar"))
            self.stop_cycle()


class Dev(Membro):
    def __init__(self, agt_name=None):
        super().__init__(agt_name)
        self.versao = 0

    @pl(gain, Goal("implementar", (Any, Any)))
    def implementar(self, src, args):
        self.feature = args[0]
        self.print(f"recebi tarefa '{self.feature}' de {src}; consultando convencao na Memoria")
        self.send("Memoria", askOne, Belief("convencao", Any))

    @pl(gain, Belief("convencao", Any))
    def implementar_v1(self, src, convencao):
        self.versao += 1
        self.print(f"implementando {self.feature} v{self.versao} seguindo '{convencao}'")
        sleep(0.5)
        self.add(Goal("entregar_codigo", (self.feature, self.versao, "senha_texto")))

    @pl(gain, Goal("corrigir", (Any, Any, Any)))
    def corrigir(self, src, args):
        self.print(f"correcao pedida por {src}: {args[2]}; buscando licao na Memoria")
        self.send("Memoria", askOne, Belief("licao", Any))

    @pl(gain, Belief("licao", Any))
    def implementar_correcao(self, src, licao):
        self.versao += 1
        self.print(f"aplicando licao '{licao}' em v{self.versao}")
        sleep(0.5)
        codigo = (self.feature, self.versao, "senha_hash")
        if self.get(Plan, Goal("autoteste", (Any, Any, Any))):
            self.add(Goal("autoteste", codigo))
        else:
            self.add(Goal("entregar_codigo", codigo))

    @pl(gain, Goal("entregar_codigo", (Any, Any, Any)))
    def entregar_codigo(self, src, codigo):
        self.send("Orquestrador", tell, Belief("codigo_pronto", codigo))

    @pl(gain, Belief("encerrar"))
    def encerrar(self, src):
        self.stop_cycle()


class QA(Membro):
    @pl(gain, Goal("testar", (Any, Any, Any)))
    def testar(self, src, codigo):
        feature, versao, senha = codigo
        self.print(f"testando {feature} v{versao}...")
        sleep(0.5)
        if senha == "senha_texto":
            self.send("Memoria", tell, Belief("licao", "senha deve ser salva com hash (bcrypt)"))
            self.send("Dev", tellHow, self.get(Plan, Goal("autoteste", (Any, Any, Any))))
            resultado = (feature, versao, "reprovado", "senha salva em texto puro")
        else:
            resultado = (feature, versao, "aprovado", "todos os testes passaram")
        self.send(src, tell, Belief("resultado_teste", resultado))

    @pl(gain, Goal("autoteste", (Any, Any, Any)))
    def autoteste(self, src, codigo):
        ok = codigo[2] == "senha_hash"
        self.print(f"[plano do QA] autoteste v{codigo[1]}: {'ok' if ok else 'falhou'}")
        self.add(Goal("entregar_codigo", codigo))

    @pl(gain, Belief("encerrar"))
    def encerrar(self, src):
        self.stop_cycle()


if __name__ == "__main__":
    Channel().show_exec = True
    Memoria("Memoria")
    Dev("Dev")
    QA("QA")
    orq = Orquestrador("Orquestrador")
    orq.add(Goal("entregar", ("login", "tela de login com e-mail e senha")))
    Admin().start_system()
