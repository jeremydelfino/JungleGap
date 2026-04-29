"""
services/riot_limiter.py
Rate limiter global pour les appels à l'API Riot.

Limites par défaut alignées sur une clé de DEV :
  - 20 requêtes / 1 seconde
  - 100 requêtes / 2 minutes

On garde 80 % de marge pour absorber les pics imprévus.
Toutes les fonctions qui tapent l'API Riot doivent passer par
`async with riot_limiter:` avant d'envoyer la requête.
"""
import asyncio
import time
import logging
from collections import deque

logger = logging.getLogger(__name__)


class RiotRateLimiter:
    """
    Token bucket double : court terme (1s) + long terme (2min).
    Concurrent-safe via lock asyncio.
    """
    def __init__(
        self,
        per_second_limit: int = 16,        # 20 réel - 20% marge
        per_two_min_limit: int = 80,       # 100 réel - 20% marge
    ):
        self._short_limit  = per_second_limit
        self._short_window = 1.0
        self._long_limit   = per_two_min_limit
        self._long_window  = 120.0

        self._short_calls: deque = deque()
        self._long_calls:  deque = deque()
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Attend qu'un slot soit disponible avant de retourner."""
        while True:
            async with self._lock:
                now = time.monotonic()

                # Purge les appels hors fenêtre
                while self._short_calls and now - self._short_calls[0] > self._short_window:
                    self._short_calls.popleft()
                while self._long_calls and now - self._long_calls[0] > self._long_window:
                    self._long_calls.popleft()

                short_ok = len(self._short_calls) < self._short_limit
                long_ok  = len(self._long_calls)  < self._long_limit

                if short_ok and long_ok:
                    self._short_calls.append(now)
                    self._long_calls.append(now)
                    return

                # Calcule combien il faut attendre pour libérer un slot
                wait_short = (self._short_calls[0] + self._short_window - now) if not short_ok else 0
                wait_long  = (self._long_calls[0]  + self._long_window  - now) if not long_ok  else 0
                wait = max(wait_short, wait_long, 0.05)

            logger.debug(f"[riot_limiter] saturé, attente {wait:.2f}s "
                         f"(short={len(self._short_calls)}/{self._short_limit}, "
                         f"long={len(self._long_calls)}/{self._long_limit})")
            await asyncio.sleep(wait)

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, *args):
        return False


# Instance globale, à importer partout
riot_limiter = RiotRateLimiter()