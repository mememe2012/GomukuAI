import os, shutil, ctypes, sys
from rich.console import Console

CONSOLE = Console()

class System:
    def ClearDir(self, directory):
        """清空目录中的所有文件和子目录，如果目录不存在则创建它。"""
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
        else:
            os.makedirs(directory, exist_ok=True)
    
    def CheckAdmin(self):
        """检查当前用户是否具有管理员权限。"""
        try:
            is_admin = os.getuid() == 0
        except AttributeError:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        return is_admin
    
    def GetAdmin(self):
        """为当前进程申请管理员权限。不新开始一个进程，而是提升当前进程的权限。"""
        if not self.CheckAdmin():
            if os.name == 'nt':
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
            elif os.name == 'posix':
                os.execvp('sudo', ['sudo', sys.executable] + sys.argv)
            elif os.name == 'darwin':
                os.execvp('osascript', ['osascript', '-e', 'do shell script "sudo python3 %s" with administrator privileges' % sys.argv[0]])
            else:
                CONSOLE.print("Unsupported system: %s" % os.name, style="red")

def test():
    s = System()
    s.ClearDir("test")
    s.GetAdmin()

if __name__ == '__main__':
    test()
