# Projet VISI201 : Le Bytecode python
De MARZIN Simon et PERIVOLAS Baptiste

# Mini-Interpréteur Python - VM

## Partie de Simon

⚠️ **Remarque importante**  
Le code propre et stable de la VM, incluant les fonctions, les conditions et la gestion des frames, se trouve sur la **branche `simon`**.  
La branche **`dev`** contient le code en développement, avec des expérimentations et des fonctionnalités à tester.

---

## Structure principale

### 1. Bytecode
Contient la liste des instructions à exécuter.

### 2. Frame
Chaque frame représente un contexte d’exécution :
- sa propre stack
- ses variables locales
- son pointeur dans le bytecode

### 3. Gestion des fonctions
- `MAKE_FUNCTION` : enregistre une fonction avec son bytecode  
- `CALL_FUNCTION` : crée un nouveau frame pour exécuter la fonction  
- `RETURN_VALUE` : récupère la valeur et revient au frame précédent

### 4. Gestion des conditions
- `COMPARE_OP` : compare deux valeurs sur la stack  
- `POP_JUMP_IF_FALSE` / `POP_JUMP_IF_TRUE` : saute selon la condition

### 5. Gestion des boucles
- `JUMP_ABSOLUTE` : revient à un indice précis dans le bytecode  
- Permet d’implémenter `while` ou `for` facilement

### 6. Branches Git

| Branche | Description |
|---------|-------------|
| `simon` | Code propre et stable avec fonctions, frames, conditions et boucles |
| `dev`   | Code en développement avec expérimentations diverses |

### 7. Exemple conceptuel de boucle `while` dans la mini-VM
- Initialisation d’une variable (ex : i = 0)
- Début de boucle : test condition sur la stack
- Si condition fausse → sortie de boucle
- Sinon : exécution du corps
- Retour au début de boucle avec `JUMP_ABSOLUTE`
- Résultat final sur la stack

---

## Conclusion
Le code de la **branche `simon`** est la base propre et fonctionnelle de la VM.  
La **branche `dev`** est destinée aux expérimentations et aux évolutions (tests de nouvelles fonctionnalités, refactorings, etc.).