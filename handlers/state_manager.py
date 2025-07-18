"""
Gestor de estados de conversación para usuarios de WhatsApp.
Mantiene el contexto de la conversación y maneja timeouts.
"""

import time
from threading import Timer
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class UserState(Enum):
    """Estados posibles de un usuario en la conversación."""
    IDLE = "idle"
    AWAITING_PART_SEARCH = "awaiting_part_search"
    AWAITING_STATUS_SEARCH = "awaiting_status_search"
    AWAITING_ORDER_NUMBER = "awaiting_order_number"
    POST_CONSULTATION = "post_consultation"
    POST_STATUS = "post_status"
    POST_ORDER = "post_order"


@dataclass
class UserSession:
    """Representa una sesión de usuario con su estado y datos."""
    state: UserState = UserState.IDLE
    data: Dict[str, Any] = field(default_factory=dict)
    last_interaction: float = field(default_factory=time.time)
    timer: Optional[Timer] = None


class StateManager:
    """
    Gestor centralizado de estados de usuario.
    
    Responsabilidades:
    - Mantener el estado de cada usuario
    - Manejar timeouts automáticos
    - Proporcionar contexto para las conversaciones
    - Limpiar sesiones inactivas
    """
    
    def __init__(self, timeout_seconds: int = 300):  # 5 minutos por defecto
        self._sessions: Dict[str, UserSession] = {}
        self.timeout_seconds = timeout_seconds
    
    def get_user_state(self, user_number: str) -> Optional[UserState]:
        """
        Obtiene el estado actual de un usuario.
        
        Args:
            user_number: Número de teléfono del usuario
            
        Returns:
            Estado actual del usuario o None si no tiene sesión activa
        """
        session = self._sessions.get(user_number)
        if session and session.state != UserState.IDLE:
            return session.state
        return None
    
    def set_user_state(self, user_number: str, state: UserState, data: Dict[str, Any] = None) -> None:
        """
        Establece el estado de un usuario y reinicia su timeout.
        
        Args:
            user_number: Número de teléfono del usuario
            state: Nuevo estado del usuario
            data: Datos adicionales para almacenar en la sesión
        """
        # Cancelar timer anterior si existe
        if user_number in self._sessions and self._sessions[user_number].timer:
            self._sessions[user_number].timer.cancel()
        
        # Crear o actualizar sesión
        session = self._sessions.get(user_number, UserSession())
        session.state = state
        session.last_interaction = time.time()
        
        if data:
            session.data.update(data)
        
        # Establecer nuevo timer de timeout
        if state != UserState.IDLE:
            session.timer = Timer(self.timeout_seconds, self._timeout_user, args=[user_number])
            session.timer.start()
        
        self._sessions[user_number] = session
        
        print(f"[🔄 STATE] Usuario {user_number} -> {state.value}")
    
    def clear_user_state(self, user_number: str) -> None:
        """
        Limpia el estado de un usuario y cancela su timeout.
        
        Args:
            user_number: Número de teléfono del usuario
        """
        if user_number in self._sessions:
            session = self._sessions[user_number]
            
            # Cancelar timer si existe
            if session.timer:
                session.timer.cancel()
            
            # Resetear a estado idle
            session.state = UserState.IDLE
            session.data.clear()
            session.timer = None
            
            print(f"[🧹 STATE] Usuario {user_number} -> limpiado")
    
    def get_user_data(self, user_number: str, key: str, default: Any = None) -> Any:
        """
        Obtiene un dato específico de la sesión del usuario.
        
        Args:
            user_number: Número de teléfono del usuario
            key: Clave del dato a obtener
            default: Valor por defecto si no existe
            
        Returns:
            Valor del dato o default si no existe
        """
        session = self._sessions.get(user_number)
        if session:
            return session.data.get(key, default)
        return default
    
    def set_user_data(self, user_number: str, key: str, value: Any) -> None:
        """
        Establece un dato específico en la sesión del usuario.
        
        Args:
            user_number: Número de teléfono del usuario
            key: Clave del dato
            value: Valor a almacenar
        """
        if user_number not in self._sessions:
            self._sessions[user_number] = UserSession()
        
        self._sessions[user_number].data[key] = value
        self._sessions[user_number].last_interaction = time.time()
    
    def update_last_interaction(self, user_number: str) -> None:
        """
        Actualiza el timestamp de la última interacción del usuario.
        
        Args:
            user_number: Número de teléfono del usuario
        """
        if user_number in self._sessions:
            self._sessions[user_number].last_interaction = time.time()
    
    def get_active_users_count(self) -> int:
        """
        Obtiene el número de usuarios con sesiones activas.
        
        Returns:
            Número de usuarios con estado diferente a IDLE
        """
        return sum(1 for session in self._sessions.values() 
                  if session.state != UserState.IDLE)
    
    def get_user_session_info(self, user_number: str) -> Dict[str, Any]:
        """
        Obtiene información completa de la sesión de un usuario.
        
        Args:
            user_number: Número de teléfono del usuario
            
        Returns:
            Diccionario con información de la sesión
        """
        session = self._sessions.get(user_number)
        if not session:
            return {"state": "no_session", "active": False}
        
        time_since_interaction = time.time() - session.last_interaction
        
        return {
            "state": session.state.value,
            "active": session.state != UserState.IDLE,
            "data_keys": list(session.data.keys()),
            "last_interaction_seconds_ago": int(time_since_interaction),
            "has_timer": session.timer is not None
        }
    
    def cleanup_inactive_sessions(self, max_age_seconds: int = 3600) -> int:
        """
        Limpia sesiones inactivas más antiguas que max_age_seconds.
        
        Args:
            max_age_seconds: Edad máxima en segundos para mantener una sesión
            
        Returns:
            Número de sesiones limpiadas
        """
        current_time = time.time()
        cutoff_time = current_time - max_age_seconds
        
        users_to_remove = []
        
        for user_number, session in self._sessions.items():
            if session.last_interaction < cutoff_time:
                # Cancelar timer si existe
                if session.timer:
                    session.timer.cancel()
                users_to_remove.append(user_number)
        
        # Remover sesiones antiguas
        for user_number in users_to_remove:
            del self._sessions[user_number]
        
        if users_to_remove:
            print(f"[🧹 CLEANUP] Limpiadas {len(users_to_remove)} sesiones inactivas")
        
        return len(users_to_remove)
    
    def _timeout_user(self, user_number: str) -> None:
        """
        Callback interno para manejar timeout de usuario.
        
        Args:
            user_number: Número de teléfono del usuario que hizo timeout
        """
        if user_number in self._sessions:
            print(f"[⏰ TIMEOUT] Usuario {user_number} hizo timeout")
            self.clear_user_state(user_number)
            
            # Aquí podrías enviar un mensaje de timeout al usuario si lo deseas
            # self.whatsapp_service.send_timeout_message(user_number)
    
    def get_all_sessions_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen de todas las sesiones activas.
        
        Returns:
            Diccionario con estadísticas de las sesiones
        """
        total_sessions = len(self._sessions)
        active_sessions = self.get_active_users_count()
        current_time = time.time()
        
        states_count = {}
        for session in self._sessions.values():
            state_name = session.state.value
            states_count[state_name] = states_count.get(state_name, 0) + 1
        
        avg_session_age = 0
        if self._sessions:
            total_age = sum(current_time - session.last_interaction 
                          for session in self._sessions.values())
            avg_session_age = total_age / len(self._sessions)
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "states_distribution": states_count,
            "average_session_age_seconds": int(avg_session_age),
            "timeout_seconds": self.timeout_seconds
        }