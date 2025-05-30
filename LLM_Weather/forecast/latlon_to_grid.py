import math

# KMA 격자변환 공식으로 위도 경도를 격자 좌표로 반환한다.
def latlon_to_grid(lat, lon):
    
    RE, GRID = 6371.00877, 5.0
    SLAT1, SLAT2 = 30.0, 60.0
    OLON, OLAT = 126.0, 38.0
    XO, YO = 43, 136
    DEGRAD = math.pi/180.0

    re = RE/GRID
    slat1, slat2 = SLAT1*DEGRAD, SLAT2*DEGRAD
    olon, olat = OLON*DEGRAD, OLAT*DEGRAD

    sn = math.log(math.cos(slat1)/math.cos(slat2)) / \
         math.log(math.tan(math.pi*0.25+slat2*0.5)/math.tan(math.pi*0.25+slat1*0.5))
    sf = (math.tan(math.pi*0.25+slat1*0.5)**sn * math.cos(slat1)) / sn
    ro = re * sf / (math.tan(math.pi*0.25+olat*0.5)**sn)

    ra = re * sf / (math.tan(math.pi*0.25+lat*DEGRAD*0.5)**sn)
    theta = lon*DEGRAD - olon
    # θ 보정
    if theta > math.pi:   theta -= 2*math.pi
    if theta < -math.pi:  theta += 2*math.pi
    theta *= sn

    x = int(ra * math.sin(theta) + XO + 0.5)
    y = int(ro - ra * math.cos(theta) + YO + 0.5)
    return x, y