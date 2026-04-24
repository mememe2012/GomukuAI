import pgmore_sys as pgs
import pgmore_screen as pgr
import pgmore_web as pgw

class System:
    def __init__(self):
        self.sys = pgs.System()
    
    def ClearDir(self, directory):
        self.sys.ClearDir(directory)

    def CheckAdmin(self):
        return self.sys.CheckAdmin()
    
    def GetAdmin(self):
        self.sys.GetAdmin()
        