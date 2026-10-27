from time import sleep

from maspy import *

from Base_Ag import Membro


class Coordenador(Membro):
    def __init__(self, name, map: Environment):
        super().__init__(name)
        self.filter_perceptions(add, focus, self.my_name)
        self.connect_to(map)
        self.capturas = []

    @pl(gain, Goal("iniciar"))
    def iniciar(self, src):
        alvos = self.listar_alvos()
        self.walkers = self.list_agents("Walker") or []
        self.print(f"alvos {alvos} para {len(self.walkers)} walkers")
        self.send("Memoria", tell, [Belief("alvo", a) for a in alvos])
        self.send(self.walkers, tell, [Belief("alvo", a) for a in alvos])
        self.send(self.walkers, achieve, Goal("move"))

    @pl(gain, Belief("captura", (Any, Any, Any, Any)))
    def captura(self, src, args):
        walker, x, y, valor = args
        self.capturas.append((valor, walker))
        self.print(f"{src} confirmou: {walker} levou o alvo {valor}")
        self.send("Memoria", tell, Belief("capturado", args))
        self.send("Memoria", untell, Belief("alvo", (x, y, valor)))
        rivais = [w for w in self.walkers if w != walker]
        self.send(rivais, untell, Belief("alvo", (x, y, valor)))

        if not self.listar_alvos():
            ranking = sorted(self.capturas, reverse=True)
            self.print("fim da disputa: " + ", ".join(f"{w}={v}" for v, w in ranking))
            sleep(0.5)
            self.send(broadcast, tell, Belief("encerrar"))
            self.stop_cycle()


class Memoria(Membro):
    @pl(gain, Belief("alvo", (Any, Any, Any)))
    def registrar_alvo(self, src, alvo):
        self.print(f"registrado alvo {alvo[2]} em {alvo[:2]} (de {src})")

    @pl(lose, Belief("alvo", (Any, Any, Any)))
    def alvo_encerrado(self, src, alvo):
        self.print(f"alvo {alvo[2]} saiu da lista de livres (untell de {src})")

    @pl(gain, Belief("capturado", (Any, Any, Any, Any)))
    def registrar_captura(self, src, args):
        self.print(f"placar: {args[0]} capturou o alvo {args[3]} em {args[1:3]}")

    @pl(gain, Belief("encerrar"))
    def encerrar(self, src):
        paredes = {b.values for b in self.get(Belief("parede", (Any, Any)), all=True, ck_src=False) or []}
        self.print(f"memoria final: {len(paredes)} paredes descobertas pelos walkers")
        self.stop_cycle()


class Juiz(Membro):
    def __init__(self, name, map: Environment):
        super().__init__(name)
        self.filter_perceptions(add, focus, self.my_name)
        self.connect_to(map)

    @pl(gain, Goal("validar_captura", (Any, Any, Any)))
    def validar(self, src, alvo):
        x, y, valor = alvo
        ok, info = self.capturar(src, x, y, valor)
        if ok:
            self.print(f"captura de {src} no alvo {valor} VALIDA")
            self.send(src, tell, Belief("captura_confirmada", valor))
            self.send("Coordenador", tell, Belief("captura", (src, x, y, valor)))
        else:
            self.print(f"captura de {src} no alvo {valor} NEGADA: {info}")
            self.send(src, tell, Belief("captura_negada", (x, y, info)))

    @pl(gain, Belief("encerrar"))
    def encerrar(self, src):
        self.stop_cycle()
