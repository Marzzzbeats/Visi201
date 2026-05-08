# VISI201 — Étude du Bytecode Python et création d’un mini-interpréteur

Projet réalisé par **MARZIN Simon** et **PERIVOLAS Baptiste**

---

# Description du projet

Ce projet a été réalisé dans le cadre du module **VISI201** autour du fonctionnement interne de Python et plus particulièrement du **bytecode CPython**.

L’objectif principal était de comprendre comment Python transforme un fichier source `.py` en instructions exécutables, puis de recréer une version simplifiée de ce fonctionnement.

Le projet prend donc un code Python simplifié en entrée, puis :

1. effectue une analyse lexicale (*lexer*) ;
2. vérifie la syntaxe (*parser*) ;
3. construit un AST (*Abstract Syntax Tree*) ;
4. compile cet AST en bytecode ;
5. puis exécute ce bytecode dans une machine virtuelle développée pour le projet.

Le bytecode utilisé est inspiré du vrai bytecode de CPython, mais reste volontairement simplifié afin de rendre son fonctionnement plus compréhensible.

---

# Fonctionnalités implémentées

Le projet prend actuellement en charge :

- les variables ;
- les opérations arithmétiques de base ;
- les comparaisons ;
- les conditions (`if`) ;
- les boucles (`while`) ;
- les fonctions ;
- les variables locales et globales ;
- une gestion simplifiée des closures ;
- certaines structures comme les listes et dictionnaires ;
- la fonction built-in `print()`.

---

# Architecture générale du projet

## Compilation

La partie compilation est composée de plusieurs étapes :

### Lexer
Transforme le texte brut en une suite de tokens.

### Parser
Vérifie la syntaxe des tokens selon les règles du langage.

### AST
Construit une représentation arborescente et logique du programme.

### Compilation en bytecode
Transforme l’AST en une suite d’instructions exécutables par la machine virtuelle.

---

## Machine virtuelle

La machine virtuelle exécute le bytecode instruction par instruction.

Elle repose principalement sur :

- une pile d’exécution ;
- des frames représentant les contextes d’exécution ;
- des objets bytecode ;
- un système simplifié de gestion des appels de fonctions.

Quelques instructions importantes :

| Instruction | Rôle |
|---|---|
| `LOAD_CONST` | Charge une constante |
| `LOAD_NAME` | Charge une variable |
| `STORE_NAME` | Stocke une variable |
| `BINARY_OP` | Effectue une opération |
| `COMPARE_OP` | Effectue une comparaison |
| `POP_JUMP_IF_FALSE` | Jump conditionnel |
| `JUMP_ABSOLUTE` | Jump inconditionnel |
| `MAKE_FUNCTION` | Crée une fonction |
| `CALL` | Appelle une fonction |
| `RETURN_VALUE` | Retourne une valeur |

---

# Structure du projet
```text
cpython/
├── lexer.py
├── parser.py
├── ast_node.py
├── code_objet.py
├── mini_interpreteur.py
├── scope.py
└── AI_miscs/
```

| Fichier | Rôle |
|---|---|
| `lexer.py` | Analyse lexicale |
| `parser.py` | Parsing et création de l’AST |
| `ast_node.py` | Définition des nœuds AST |
| `code_objet.py` | Compilation en bytecode |
| `mini_interpreteur.py` | Machine virtuelle |
| `scope.py` | Gestion des scopes et closures |

---

# État actuel du projet

## Try / Except

La gestion des `try/except` est partiellement implémentée.

La compilation des structures existe en partie, mais leur exécution n’est pas encore prise en charge correctement dans la machine virtuelle.

---

## Closures

Les closures sont partiellement fonctionnelles.

Le compilateur utilise une logique proche de CPython avec des variables libres (*freevars*) et des cellules (*cellvars*).

Cependant, dans la machine virtuelle, une simplification a été faite : les closures sont transmises sous forme de dictionnaires contenant des valeurs figées.

Cela entraîne un problème important : si une variable capturée est modifiée après la création de la closure, la nouvelle valeur n’est pas propagée correctement.

Une implémentation plus fidèle nécessiterait de partager directement des objets `Cell` entre les fonctions plutôt que de copier les valeurs.

Cette simplification a été conservée afin de limiter la complexité de la VM dans le temps imparti du projet.

---

# Branches Git

| Branche | Description |
|---|---|
| `main` | Branche principale. Version stable
| `main_clean` | Main mais mieux 
| `dev` | Branche principale de développement |
| `simon` | Ancienne branche contenant une version plus stable de certaines parties de la VM |
| `baptiste` | Branche de dev pour la partie compilation et la partie gestion de connecté les fichiers entre eux
| `baptiste_clean` | baptiste mais commenté.

---

# Lancer le projet

Exécuter simplement :

```bash
python main.py
```

Le fichier source Python à analyser peut ensuite être modifié dans le dossier `sources/`.

---

# Objectif pédagogique

Ce projet avait avant tout un objectif pédagogique :

- comprendre le fonctionnement interne de Python ;
- découvrir les différentes étapes de compilation ;
- comprendre le rôle du bytecode ;
- manipuler des notions de VM, frames, piles et scopes ;
- et explorer les principes de base des compilateurs et interpréteurs.

---

# Ressources

- Documentation Python
- Documentation CPython
- Wikipédia :
  - Bytecode
  - Compilateur
  - Interpréteur
  - AST
  - Machine virtuelle

---

# Dépôt GitHub

https://github.com/Marzzzbeats/Visi201

