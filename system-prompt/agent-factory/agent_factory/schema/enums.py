# agent_factory/schema/enums.py
"""跨资源共享枚举（feature / issue 都用的才放这里；单一资源的放各自资源文件）."""
from enum import Enum


class Priority(str, Enum):
    """优先级."""
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
