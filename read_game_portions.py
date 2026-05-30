from pathlib import Path
path = Path('C:/Users/antic/OneDrive/Tài liệu/GitHub/g-me/game.py')
print('game.py exists:', path.exists())
with path.open('r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(1175, 1206):
    print(f'{i+1}: {lines[i].rstrip()}')
print('\n=== HOE ===\n')
for i in range(1230, 1329):
    print(f'{i+1}: {lines[i].rstrip()}')
