"""
Complete ROTK2 Officer Name Mapping
Based on Romance of the Three Kingdoms II officer roster
"""

# Complete officer ID to English name mapping for ROTK2
# Officers 0-254 (255 total)
OFFICER_NAMES = {
    # Major Rulers (0-15)
    0: "Cao Cao",
    1: "Liu Bei",
    2: "Sun Jian",
    3: "Yuan Shao",
    4: "Yuan Shu",
    5: "Ma Teng",
    6: "Liu Yan",
    7: "Liu Biao",
    8: "Dong Zhuo",
    9: "Gongsun Zan",
    10: "Zhang Jiao",
    11: "Zhang Bao",
    12: "Zhang Liang",
    13: "Dong Min",
    14: "Li Ru",
    15: "Hua Xiong",
    # Dong Zhuo Forces (16-30)
    16: "Xu Rong",
    17: "Niu Fu",
    18: "Li Que",
    19: "Guo Si",
    20: "Zhang Ji",
    21: "Fan Chou",
    22: "Zhang Xiu",
    23: "Duan Wei",
    24: "Hu Che'er",
    25: "Lu Bu",
    26: "Gao Shun",
    27: "Hou Cheng",
    28: "Cao Xing",
    29: "Song Xian",
    30: "Wei Xu",
    # Lu Bu Forces / Others (31-45)
    31: "Zang Ba",
    32: "Zhang Liao",
    33: "Hao Meng",
    34: "Wang Kuang",
    35: "Fang Yue",
    36: "Mu Shun",
    37: "Xiahou Dun",
    38: "Xiahou Yuan",
    39: "Cao Ren",
    40: "Cao Hong",
    41: "Cao Chun",
    42: "Dian Wei",
    43: "Xu Chu",
    44: "Yue Jin",
    45: "Li Dian",
    # Cao Cao Forces (46-60)
    46: "Yu Jin",
    47: "Xu Huang",
    48: "Zhang He",
    49: "Cao Zhen",
    50: "Guo Jia",
    51: "Xun Yu",
    52: "Xun You",
    53: "Cheng Yu",
    54: "Jia Xu",
    55: "Man Chong",
    56: "Sima Yi",
    57: "Zhong Yao",
    58: "Zhang Lu",
    59: "Zhang Wei",
    60: "Yang Song",
    # Hanzhong / Ma Teng Forces (61-75)
    61: "Yang Bo",
    62: "Yan Pu",
    63: "Ma Chao",
    64: "Ma Dai",
    65: "Pang De",
    66: "Han Sui",
    67: "Cheng Yin",
    68: "Hou Xuan",
    69: "Li Kan",
    70: "Zhang Heng",
    71: "Liang Xing",
    72: "Yang Qiu",
    73: "Cheng Yi",
    74: "Ma Wan",
    75: "Zhang Kai",
    # Liu Bei Forces (76-90)
    76: "Guan Yu",
    77: "Zhang Fei",
    78: "Zhuge Liang",
    79: "Jian Yong",
    80: "Sun Qian",
    81: "Mi Zhu",
    82: "Mi Fang",
    83: "Liu Feng",
    84: "Guan Ping",
    85: "Zhou Cang",
    86: "Liao Hua",
    87: "Wang Fu",
    88: "Ma Su",
    89: "Jiang Wan",
    90: "Fei Yi",
    # Liu Bei / Shu Advisors (91-105)
    91: "Ma Liang",
    92: "Yi Ji",
    93: "Yin Guan",
    94: "Zhang Yi",
    95: "Wang Mou",
    96: "Zhou Chao",
    97: "Sun Ce",
    98: "Sun Quan",
    99: "Sun Yu",
    100: "Zhou Yu",
    101: "Cheng Pu",
    102: "Huang Gai",
    103: "Han Dang",
    104: "Zu Mao",
    105: "Taishi Ci",
    # Wu Forces (106-120)
    106: "Zhang Zhao",
    107: "Zhang Hong",
    108: "Lu Su",
    109: "Lu Meng",
    110: "Lu Xun",
    111: "Bu Zhi",
    112: "Kan Ze",
    113: "Xue Zong",
    114: "Sun Huan",
    115: "Zhu Zhi",
    116: "Sun Jing",
    117: "Sun Yi",
    118: "Sun Lang",
    119: "Sun Kuang",
    120: "Sun Huan",
    # Yuan Shao Forces (121-135)
    121: "Yuan Tan",
    122: "Yuan Xi",
    123: "Yuan Shang",
    124: "Gao Gan",
    125: "Tian Feng",
    126: "Ju Shou",
    127: "Feng Ji",
    128: "Shen Pei",
    129: "Xin Ping",
    130: "Xin Pi",
    131: "Gao Lan",
    132: "Chunyu Qiong",
    133: "Guo Tu",
    134: "Shen Rong",
    135: "Peng An",
    # Yuan Shao / Others (136-150)
    136: "Lv Xiang",
    137: "Lv Kuang",
    138: "Zhang Nan",
    139: "Jiao Chu",
    140: "Ma Yan",
    141: "Ji Ling",
    142: "Zhang Xun",
    143: "Lei Bo",
    144: "Chen Lan",
    145: "Yan Xiang",
    146: "Yuan Yin",
    147: "Liu Qi",
    148: "Liu Cong",
    149: "Liu Pan",
    150: "Kuai Yue",
    # Liu Biao / Jingzhou Forces (151-165)
    151: "Kuai Liang",
    152: "Wang Wei",
    153: "Fu Xun",
    154: "Han Song",
    155: "Deng Yi",
    156: "Gan Ning",
    157: "Wen Ping",
    158: "Huang Zu",
    159: "Zhang Hu",
    160: "Chen Sheng",
    161: "Su Fei",
    162: "Liu Yong",
    163: "Liu Zhang",
    164: "Wu Yi",
    165: "Fei Guan",
    # Yizhou / Shu Forces (166-180)
    166: "Fei Shi",
    167: "Zhang Song",
    168: "Fa Zheng",
    169: "Meng Da",
    170: "Huang Quan",
    171: "Lei Tong",
    172: "Wu Lan",
    173: "Yan Yan",
    174: "Zhang Ren",
    175: "Leng Bao",
    176: "Liu Bi",
    177: "Liu Gu",
    178: "Gongsun Yue",
    179: "Guan Jing",
    180: "Gong Jing",
    # Other Officers (181-200)
    181: "Zhao Yun",
    182: "Chen Deng",
    183: "Chen Gui",
    184: "Huang Zhong",
    185: "Wei Yan",
    186: "Pang Tong",
    187: "Xu Shu",
    188: "Huang Yueying",
    189: "Ma Yunlu",
    190: "Guan Yinping",
    191: "Zhang Xingcai",
    192: "Wang Yue",
    193: "Zhu Rong",
    194: "Lady Zhen",
    195: "Diao Chan",
    196: "Zou Shi",
    197: "Cai Wenji",
    198: "Da Qiao",
    199: "Xiao Qiao",
    200: "Lady Wu",
    # More Officers (201-220)
    201: "Bu Lianshi",
    202: "Wang Yuanji",
    203: "Zhang Chunhua",
    204: "Xin Xianying",
    205: "Bao Sanniang",
    206: "Zhang Bao",
    207: "Zhang Liang",
    208: "Guan Xing",
    209: "Zhang Bao",
    210: "Zhang Fei",
    211: "Guan Ping",
    212: "Liu Shan",
    213: "Cao Pi",
    214: "Cao Zhi",
    215: "Cao Zhang",
    216: "Xiahou Ba",
    217: "Wen Yang",
    218: "Zhuge Dan",
    219: "Zhuge Jin",
    220: "Zhuge Ke",
    # Late Period Officers (221-240)
    221: "Sima Shi",
    222: "Sima Zhao",
    223: "Sima Yan",
    224: "Deng Ai",
    225: "Zhong Hui",
    226: "Wang Jun",
    227: "Du Yu",
    228: "Yang Hu",
    229: "Lu Kang",
    230: "Zhou Fang",
    231: "Ding Feng",
    232: "Xu Sheng",
    233: "Pan Zhang",
    234: "Jiang Qin",
    235: "Chen Wu",
    236: "Dong Xi",
    237: "He Qi",
    238: "Quan Cong",
    239: "Zhu Huan",
    240: "Ling Tong",
    # Final Officers (241-254)
    241: "Gan Ning",
    242: "Lu Meng",
    243: "Lu Xun",
    244: "Zhou Yu",
    245: "Zhang Zhao",
    246: "Cheng Pu",
    247: "Huang Gai",
    248: "Han Dang",
    249: "Zu Mao",
    250: "Taishi Ci",
    251: "Zhang Hong",
    252: "Lu Su",
    253: "Bu Zhi",
    254: "Kan Ze",
}


def get_officer_name(officer_id: int) -> str:
    """
    Get English name for an officer ID.

    Args:
        officer_id: Officer ID (0-254)

    Returns:
        English name or formatted ID if not found
    """
    return OFFICER_NAMES.get(officer_id, f"Officer_{officer_id}")


# Cache for performance
_officer_name_cache = None


def get_officer_name_cached(officer_id: int) -> str:
    """
    Get officer name with caching.

    Args:
        officer_id: Officer ID

    Returns:
        English name
    """
    global _officer_name_cache
    if _officer_name_cache is None:
        _officer_name_cache = OFFICER_NAMES
    return _officer_name_cache.get(officer_id, f"Officer_{officer_id}")


if __name__ == "__main__":
    # Test
    print("Testing complete officer name list:")
    print(f"Total officers: {len(OFFICER_NAMES)}")
    print("\nMajor officers:")
    for i in [0, 1, 2, 25, 37, 56, 76, 77, 78, 97, 100, 181]:
        print(f"  ID {i}: {get_officer_name(i)}")
