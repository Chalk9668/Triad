import sys
import math
from fractions import Fraction
from dataclasses import dataclass, field
from typing import Optional
import ast
import operator

# 定義部

# 三角形をABCとする。
# その対辺をabcとする。

# 文字の宣言

# 3辺をabcとして定義する。
# abcの初期化処理
a = float(0)
b = float(0)
c = float(0)

# 各々の角（rad.）をABCとして定義する。
# ABCの初期化処理
A = float(0)
B = float(0)
C = float(0)

# 各々のcos角をcosA, cosB, cosCとして定義する。
# cosA, cosB, cosCの初期化処理
cosA = float(0)
cosB = float(0)
cosC = float(0)

# 各々のsin角をsinA, sinB, sinCとして定義する。
# sinA, sinB, sinCの初期化処理
sinA = float(0)
sinB = float(0)
sinC = float(0)

# 元からある点
ORIGINAL_POINT_NAMES = ["A", "B", "C"]

# 元からある辺
ORIGINAL_SIDE_NAMES  = ["a", "b", "c"]

#それぞれの側と点が持つ外分点の名前、成す線分の名前、またその長さ（但し持つ点からの長さ）をextDivと定義する。
@dataclass
class ExtDiv:
    pointName: str
    distance: float
    lineName: str

# 辺aの持つ点とその長さについてextPoint_aと定義する。
@dataclass
class ExtPoint_a:
    lengh: float
    startWithB: list[ExtDiv] = field(default_factory=list)
    startWithC: list[ExtDiv] = field(default_factory=list)

# 辺bの持つ点とその長さについてextPoint_bと定義する
@dataclass
class ExtPoint_b:
    lengh: float
    startWithC: list[ExtDiv] = field(default_factory=list)
    startWithA: list[ExtDiv] = field(default_factory=list)

# 辺cの持つ点とその長さについてextPoint_cと定義する
@dataclass
class ExtPoint_c:
    lengh: float
    startWithA: list[ExtDiv] = field(default_factory=list)
    startWithB: list[ExtDiv] = field(default_factory=list)

# 辺abcについての全ての情報を持つ親クラスをAllTriadSideと定義する。
@dataclass
class AllTriadSide:
    a: ExtPoint_a
    b: ExtPoint_b
    c: ExtPoint_c

#仮の値（変更ごとに捨てる）
temp_ratio_Fraction = Fraction(0) # 有理数比
temp_ratio_float = float(0)
temp_side = str()
temp_point = str()
temp_newPoint = str()
temp_newLine = str()



# 関数の宣言

# 絶対に全部の出す以外で使うな！！！！（エラーが出かねないので）
# 余弦定理によるcos角Cの導出
def cos_angle_C(a, b, c):
    _cosC = (a**2 + b**2 - c**2) / (2 * a * b)       
    return _cosC

# 余弦定理によるcos角Bの導出   
def cos_angle_B(a, b, c):
    _cosB = (a**2 + c**2 - b**2) / (2 * a * c)
    return _cosB

# 余弦定理によるcos角Aの導出 
def cos_angle_A(a, b, c):
    _cosA = (b**2 + c**2 - a**2) / (2 * b * c)
    return _cosA

# 全部のcos角の値を出す
def all_cos_angles(a, b, c):
    global cosA, cosB, cosC
    cosA = cos_angle_A(a, b, c)
    cosB = cos_angle_B(a, b, c)
    cosC = cos_angle_C(a, b, c)

# 初期値のぶちこみ（4:5:6)
def initialize_TonicMajorThird():
    global a, b, c          
    a = 4
    b = 5
    c = 6

# 外分点作成
# side  : Triad.a / Triad.b / Triad.c のいずれか
# start : 起点の頂点名 ("A" / "B" / "C")。その頂点から辺の反対側へ伸ばす
# ratio : 辺の長さに対する倍率(distance = ratio * 辺の長さ)
# floatで渡せ！！！！！！！
def make_externalDivisionPoint(side, start, ratio, pointName, lineName):
    attr = "startWith" + start
    if not hasattr(side, attr): 
        raise ValueError(f"この辺は頂点{start}を起点にできません")
    distance = ratio * side.lengh
    getattr(side, attr).append(ExtDiv(pointName, distance, lineName))

# 点の存在を判定
def pointExists(triad, name):
    if name in ORIGINAL_POINT_NAMES:
        return True
    for side in (triad.a, triad.b, triad.c):
        for value in vars(side).values():
            if isinstance(value, list):          # lengh(float)は飛ばす
                for d in value:
                    if d.pointName == name:
                        return True
    return False

# 線分の存在を判定
def lineExists(triad, name):
    if name in ORIGINAL_SIDE_NAMES:
        return True
    for side in (triad.a, triad.b, triad.c):
        for value in vars(side).values():
            if isinstance(value, list):         # lengh(float)は飛ばす
                for d in value:
                    if d.lineName == name:
                        return True
    return False


# 余弦定理で、指定した二辺から成る三角形の残りの一辺を求める
# name1, name2 : 元の辺("a"/"b"/"c") と 外分点名("P"など) を1つずつ(順不同)
#                外分点名は「起点→その外分点」の線分(長さ distance)を表す
# 戻り値 : (長さ, (端点, 端点))

# 辺ごとの端点(a=BC, b=CA, c=AB)
SIDE_VERTICES = {"a": ("B", "C"), "b": ("C", "A"), "c": ("A", "B")}

# 例外: 既に長さが分かっている辺を求めようとした
class SideAlreadyKnownError(Exception):
    pass

# 例外: 三角形を作れない組み合わせ(共通の頂点がない、同一直線上、など)
class InvalidSidePairError(Exception):
    pass

# 外分点の名前から (どの辺か, 起点の頂点, ExtDiv) を探す。無ければ None
def find_extDiv(triad, name):
    for sideName in ORIGINAL_SIDE_NAMES:
        side = getattr(triad, sideName)
        for attr, value in vars(side).items():
            if attr.startswith("startWith"):          # lengh(float)は飛ばす
                for d in value:
                    if d.pointName == name or d.lineName == name:
                        return sideName, attr[-1], d  # attr[-1] は "A"/"B"/"C"
    return None

def solve_third_side(triad, name1, name2):
    kinds = []
    for n in (name1, name2):
        if n in ORIGINAL_SIDE_NAMES:
            kinds.append(("side", n))
        else:
            found = find_extDiv(triad, n)
            if found is None:
                raise InvalidSidePairError(f"{n} は辺でも外分点でもありません。やり直せ")
            kinds.append(("ext", found))

    # 元の辺どうし → 残りの一辺は元の三角形の辺で、既知
    if kinds[0][0] == "side" and kinds[1][0] == "side":
        raise SideAlreadyKnownError("元の三角形の辺どうしから成る辺は、既に求められています")
    # 外分点どうし → 今回は未対応
    if kinds[0][0] == "ext" and kinds[1][0] == "ext":
        s1, v1, d1 = kinds[0][1]
        s2, v2, d2 = kinds[1][1]
        if v1 != v2:
            raise InvalidSidePairError("起点の頂点が異なる外分点同士はあまり今回の研究に於いて意味がないので無視することとします。やり直せ")
        if s1 == s2:                                   # 同じ辺上 → 同一直線上
            return abs(d1.distance - d2.distance), (d1.pointName, d2.pointName)
        cos_v = {"A": cosA, "B": cosB, "C": cosC}[v1]
        L = math.sqrt(d1.distance**2 + d2.distance**2 - 2 * d1.distance * d2.distance * cos_v)
        return L, (d1.pointName, d2.pointName)

    # ここから「元の辺1本 + 外分点1つ」
    x = kinds[0][1] if kinds[0][0] == "side" else kinds[1][1]
    sideName, v, d = kinds[0][1] if kinds[0][0] == "ext" else kinds[1][1]

    if x == sideName:
        raise InvalidSidePairError("外分した辺そのものとは三角形を作れません(同一直線上)")
    if v not in SIDE_VERTICES[x]:
        raise InvalidSidePairError(f"辺{x}は頂点{v}を持たないので、共通の頂点がありません")

    e = getattr(triad, x).lengh                       # 元の辺の長さ
    cos_v = {"A": cosA, "B": cosB, "C": cosC}[v]      # 頂点vの内角のcos
    # 外分点側の角は外角(π - v)なので cos(π - v) = -cos_v
    L = math.sqrt(e**2 + d.distance**2 + 2 * e * d.distance * cos_v)

    apex = SIDE_VERTICES[x][0] if SIDE_VERTICES[x][1] == v else SIDE_VERTICES[x][1]
    return L, (apex, d.pointName)

# 汎用オペラント処理

# 比の入力文字列を評価して Fraction にする
# 分数("3/2")、小数("1.5")、無理数("sqrt(2)", "2**(1/12)")、式("(1+sqrt(5))/2")に対応
# 有理数のまま計算できる間は厳密な Fraction で保持し、無理数が出た時点で float を経由して Fraction にする
# (float → Fraction は2進表現としては厳密なので、float(Fraction) で元の float に戻る)
_BINOPS  = {ast.Add: operator.add, ast.Sub: operator.sub,
            ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow}
_UNARYOPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_CONSTS  = {"pi": math.pi, "e": math.e, "tau": math.tau}

# 平方根は、有理数で割り切れるなら Fraction のまま返す
def _sqrt_exact(x):
    x = Fraction(x)
    if x >= 0:
        n, d = math.isqrt(x.numerator), math.isqrt(x.denominator)
        if n * n == x.numerator and d * d == x.denominator:
            return Fraction(n, d)
    return math.sqrt(x)

_FUNCS = {"sqrt": _sqrt_exact, "exp": math.exp, "log": math.log,"log2": math.log2, "log10": math.log10,"sin": math.sin, "cos": math.cos, "tan": math.tan}

def _eval_node(node):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
            and not isinstance(node.value, bool):
        return Fraction(repr(node.value))     # 0.1 を 0.1 のまま(10進として厳密に)扱う
    if isinstance(node, ast.Name) and node.id in _CONSTS:
        return _CONSTS[node.id]
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARYOPS:
        return _UNARYOPS[type(node.op)](_eval_node(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        l, r = _eval_node(node.left), _eval_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(r) > 1000:
            raise ValueError("指数が大きすぎます")
        return _BINOPS[type(node.op)](l, r)   # Fraction ** Fraction(非整数) は float になる
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
            and node.func.id in _FUNCS and len(node.args) == 1 and not node.keywords:
        return _FUNCS[node.func.id](_eval_node(node.args[0]))
    raise ValueError("使えない記号・関数が含まれています")

def parse_ratio(text):
    text = text.strip().replace("^", "**").replace("π", "pi")
    value = _eval_node(ast.parse(text, mode="eval"))
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("有限の値になりません")
    return Fraction(value)

# ===============================================================================   =============================================

# 操作部
if input("長音階の1のトライアド(4:5:6)の値をぶちこむ？(y/n): ") == "y":
    initialize_TonicMajorThird()
elif input("他の値を入力する？(y/n): ") == "y":
    a = float(input("aの値を入力してください: "))
    b = float(input("bの値を入力してください: "))
    c = float(input("cの値を入力してください: "))
else:
    print("終了")
    sys.exit(1)

print("初期値をぶち込みました。")

# 三角形の存在を確認
if not abs(b - c) < a < b + c:
    print("その三角形は存在しません。やり直せ")
    sys.exit(1)

# 一旦全部のcos角の値を出しちゃう   
all_cos_angles(a, b, c)

# lengh に設定した abc の長さを入れる(インスタンス化と同時に渡す)
Triad = AllTriadSide(a = ExtPoint_a(lengh = a), b = ExtPoint_b(lengh = b), c = ExtPoint_c(lengh = c),)

#こいつをwhile True:する
def appTriad ():

    # 外分点を作る
    while True:
        ans = input("外分点を作る？ y/n ")
        
        if ans == "y":
            temp_side = input("使いたい辺を言って下さい: ")
            if not lineExists(Triad, temp_side):
                print("その辺は存在しません。やり直せ。\n")
                continue  # while Trueの先頭に戻る
            temp_point = input("外分の始点としたい既存の点を言ってください: ")
            if not pointExists(Triad, temp_point):
                print("その点は存在しません。やり直せ。\n")
                continue  # while Trueの先頭に戻る
            try:
                temp_ratio_Fraction = parse_ratio(input("外分する比を言ってください: "))
            except (ValueError, SyntaxError, ZeroDivisionError, OverflowError) as e:
                print("その比は解釈できません:", e, "\nやり直せ。\n")
                continue  # while Trueの先頭に戻る
            temp_ratio_float = float(temp_ratio_Fraction)
            temp_newPoint = input("外分点の名前を言ってください: ")
            if pointExists(Triad, temp_newPoint):
                print("その点は使われています。やり直せ。\n")
                continue  # while Trueの先頭に戻る
            temp_newLine = input("外分されたことによりできる辺を言ってください: ")
            if lineExists(Triad, temp_newLine):
                print("その辺は使われています。やり直せ。\n")
                continue  # while Trueの先頭に戻る
            
            make_externalDivisionPoint(getattr(Triad, temp_side), temp_point, temp_ratio_float, temp_newPoint, temp_newLine)
            
            # 初期化
            temp_side = str()
            temp_point = str()
            temp_ratio_float = float(0)
            temp_ratio_Fraction = Fraction(0)
            temp_newLine = str()
            temp_newPoint = str()
            break
        else:
            break

    # 余弦定理で辺を求める
    if str(input("辺を求める？ y/n ")) == "y":
        n1 = input("1つ目(元の辺 or 外分点の名前): ")
        n2 = input("2つ目(元の辺 or 外分点の名前): ")
        try:
            length, (p, q) = solve_third_side(Triad, n1, n2)
        except SideAlreadyKnownError as e:
            print("エラー:", e)
        except InvalidSidePairError as e:
            print("エラー:", e)
        else:
            print(f"{p}{q} の長さ: {length}")


while True:
    appTriad()

if __name__ == "__main__":
    main()  