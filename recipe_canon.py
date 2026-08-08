"""Kanonisk signatur för ett hantverksrecept.

Två recept krockar i hantverksrutan om de ger samma RUTNÄT AV FÖREMÅL — inte
om deras JSON råkar likna varandra. Bokstäverna i `pattern` är godtyckliga,
tomma rader/kolumner ignoreras av spelet, och ett speglat mönster matchar
också. Därför normaliseras allt hit innan jämförelse:

  shaped:    rutnätet översatt till föremåls-id, trimmat, minsta av
             (rutnätet, dess spegelbild)
  shapeless: sorterad multimängd av föremåls-id

Delas av audit.py (kollar våra recept mot vanilla + varandra) och
tools/snapshot_vanilla_recipes.py (bygger vanilla-facit från Mojangs
officiella bedrock-samples). Ändra aldrig i bara den ena änden.
"""


def ing_id(v):
    if isinstance(v, str):
        return v
    i = v.get("item") or v.get("tag", "")
    d = v.get("data")
    if d not in (None, 32767):          # 32767 = vilket data-värde som helst
        i += f"#{d}"
    return i


def canon(body):
    """Signatur för recipe_shaped/recipe_shapeless-kroppen, annars None."""
    if "pattern" in body:
        key = {k: ing_id(v) for k, v in body.get("key", {}).items()}
        grid = [[key.get(ch, "") for ch in row] for row in body["pattern"]]
        while grid and all(c == "" for c in grid[0]): grid.pop(0)
        while grid and all(c == "" for c in grid[-1]): grid.pop()
        while grid and grid[0] and all(r[0] == "" for r in grid):
            for r in grid: r.pop(0)
        while grid and grid[0] and all(r[-1] == "" for r in grid):
            for r in grid: r.pop()
        mirror = [list(reversed(r)) for r in grid]
        return "shaped:" + min(str(grid), str(mirror))
    if "ingredients" in body:
        items = []
        for i in body["ingredients"]:
            n = i.get("count", 1) if isinstance(i, dict) else 1
            items += [ing_id(i)] * n
        return "shapeless:" + str(sorted(items))
    return None
