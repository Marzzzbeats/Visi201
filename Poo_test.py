import dis

class Carte():

    def __init__(self, couleur : str, chiffre : int):
        self.color=couleur
        self.number=chiffre

    def get_col(self):
        return self.color
    
    def get_number(self):
        return self.number
    

roi = Carte("pic", 12)


print(dis.dis(Carte))