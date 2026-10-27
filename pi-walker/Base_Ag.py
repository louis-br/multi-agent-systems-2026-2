import threading

from maspy import *

_rm_de_mensagem = threading.local()


class Membro(Agent):
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
