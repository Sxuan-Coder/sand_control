import time

from utils.socket_utils import valve_controller


# 清砂控制类
class CleanSandControl:
    def __init__(self):
        """初始化清砂控制类属性"""
        self.master = None
        self.conn = None
        self.addr = None
        self.socket_client = None

    def execute_clean_sequence(self):
        """执行完整的清砂流程"""
        try:
            # 按顺序打开阀门进行清砂
            self._open_valves_sequence()

            # 按相反顺序关闭阀门
            self._close_valves_sequence()

            return True

        except Exception as e:
            print(f"清砂序列执行出错: {str(e)}")
            return False

    def _open_valves_sequence(self):
        """按顺序打开阀门"""
        # 出料口控制
        valve_controller(self.conn, '01', True)
        time.sleep(1)

        # 第一个风机控制
        valve_controller(self.conn, '06', True)
        time.sleep(0.2)

        # 第二个风机控制
        valve_controller(self.conn, '07', True)
        time.sleep(0.5)

        # 来回控制
        valve_controller(self.conn, '03', True)
        time.sleep(3.5)

    def _close_valves_sequence(self):
        """按相反顺序关闭阀门"""
        # 第二个风机控制
        valve_controller(self.conn, '07', False)
        time.sleep(0.2)

        # 第一个风机控制
        valve_controller(self.conn, '06', False)
        time.sleep(0.2)

        # 来回控制
        valve_controller(self.conn, '03', False)
        time.sleep(0.2)

        # 出料口控制
        valve_controller(self.conn, '01', False)

    def close(self):
        """关闭所有连接"""
        try:
            if self.conn:
                self.conn.close()
            if self.master:
                self.master.close()
            print("已关闭所有清砂控制连接")
        except Exception as e:
            print(f"关闭连接时出错: {str(e)}")

