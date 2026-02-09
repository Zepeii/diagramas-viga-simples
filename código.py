import numpy as np
import matplotlib.pyplot as plt
import scipy.integrate as sc
import streamlit as st
import io
import contextlib

def criar_funcao_distribuida(expr):
    allowed = {
        "x": None,
        "np": np,
        "sin": np.sin,
        "cos": np.cos,
        "exp": np.exp,
        "sqrt": np.sqrt,
        "ln": np.log
    }

    def q(x):
        local_dict = allowed.copy()
        local_dict["x"] = x
        resultado = eval(expr, {"__builtins__": {}}, local_dict)

        # GARANTIA DE ARRAY
        if np.isscalar(resultado):
            return resultado * np.ones_like(x)

        return resultado

    return q

def diagramas_viga(dic,L,apoios):
    #dic --> list[dict]  (carregamentos)
    #L --> Float   (largura da viga)
    #apoios --> list[dict]  (tipos e posições dos apoios)
    
    #exemplo de dicionário força concentrada em y {"type": "point", "x": 2.0, "value": -10.0}

    #exemplo de dicionário momento concentrado {"type": "moment", "x": 2.0, "value": -10.0}

    #exemplo de dicionário carga distribuida {"type": "distributed", "x": [2.0, 3.0], "q": lambda x: 5+3x}
        #no exemplo da carga distribuida foi utilizada uma carga trapezoidal 5+3x

    #exemplo de dicionário força concentrada em x {"type": "point_x", "x": 2.0, "value": -10.0}

    #exemplo de dicionário carga distribuida {"type": "distributed_x", "x": [2.0, 3.0], "q": lambda x: 5+3x}
        #no exemplo da carga distribuida foi utilizada uma carga trapezoidal 5+3x

    #exemplo de dicionário apoios:
    #apoios = [
    #{"x": 0.0, "Rx": True,  "Ry": True,  "Mz": False},    pino
    #{"x": 4.0, "Rx": False, "Ry": True,  "Mz": False},    rolete
    #{"x": 2.0, "Rx": True, "Ry": True, "Mz": True}]    engaste

    
    #Checando se há apoios na mesma posição:
    posicao_apoios = []
    for a in apoios:
        posicao_apoios.append(round(a["x"],3))
    
    posicao_apoios2=list(set(posicao_apoios))
    
    if len(posicao_apoios2) < len(posicao_apoios):
        return("Há mais de um apoio no mesmo ponto, rever modelagem")

    #Checando a estaticidade da viga modelada
    n_Rx = sum(a["Rx"] for a in apoios)
    n_Ry = sum(a["Ry"] for a in apoios)
    n_Mz = sum(a["Mz"] for a in apoios)



    
    if n_Rx + n_Ry + n_Mz == 3:
        print("A viga é isostática")

    if n_Rx + n_Ry + n_Mz < 3 or n_Rx == 2 or n_Ry == 3 or n_Rx == 0:
        return("A viga modelada é hipoestática, reveja a modelagem dela")

    if n_Rx + n_Ry + n_Mz > 3: 
        return("A viga modelada é hiperestática, esse programa ainda não resolve esse tipo de viga")

    
    #Cálculo das reações de apoio:
    #F é o valor da força concentrada; r é a posição de cada força
    F_point=[]
    r_point=[]

    F_moment=[]
    r_moment=[]

    F_point_x=[]
    
    #no caso das cargas distribuidas, serão trazidas a informação das suas resultantes F_uniform_res 
    #e o ponto de aplicação delas no centroide r_uniform_res
    F_distributed_res=[]
    r_distributed_res=[]

    #Esse for serve para preencher o F e o r e testar se os inputs estão certos, percorrendo cada carregamento
    for load in dic:
        if load["type"]=="point":
            F_point.append(load["value"])
            r_point.append(load["x"])
        
        if load["type"]=="moment":
            F_moment.append(load["value"])
            r_moment.append(load["x"])
        
        if load["type"]=="distributed":
            x1=load["x"][0]
            x2=load["x"][1]
            x=np.linspace(x1,x2,1000)

            q = load["q"]

            #calculo da força resultante:
            
            #trazer os valores de q(x) para uma lista quando é uma distribuição que segue uma função
            if callable(q):
                qx = q(x)

            #trazer os valores de q(x) para uma lista quando é uma distribuição é constante
            else:
                qx = q * np.ones_like(x)

            #calculo da força resultante pela integral da carga
            F_distributed_res.append(-np.trapezoid(qx, x))

            #calculo do centroide para o caso da força resultante ser =0 ou diferente de 0
            if -np.trapezoid(qx, x)==0:
                r_distributed_res.append(0)
            
            else:
                r_distributed_res.append(np.trapezoid(qx*x, x)/np.trapezoid(qx, x))

        #forças em x para reação horizontal:
        if load["type"]=="point_x":
             F_point_x.append(load["value"])
        
        if load["type"]=="distributed_x":
            x1=load["x"][0]
            x2=load["x"][1]
            x=np.linspace(x1,x2,1000)
            
            q = load["q"]

            if callable(q):
                qx=q(x)     #Caso em que é uma carga distribuida variável
            
            else:
                qx = q * np.ones_like(x)  #Caso em que é uma carga distribuida constante

            F_point_x.append(np.trapezoid(qx,x)) #Força resultante em x da carga distribuida
        
        x = load["x"]

    # Caso: força/momento concentrado
        if np.isscalar(x):
            if x < 0 or x > L:
                return "Uma ou mais forças estão fora da viga, rever a modelagem do problema"

    # Caso: carga distribuída
        else:
            x1, x2 = x
            if x1 < 0 or x2 > L or x1 > x2:
                return "Uma ou mais forças estão fora da viga, rever a modelagem do problema"
         
    F_point=np.array(F_point,dtype=float)
    r_point=np.array(r_point,dtype=float)
    
    F_distributed_res=np.array(F_distributed_res,dtype=float)
    r_distributed_res=np.array(r_distributed_res,dtype=float)
    
    F_point_x=np.array(F_point_x,dtype=float)

    #Calculando Rx:
    Rx=-np.sum(F_point_x)
    for apoio in apoios:
        if apoio["Rx"] == True:
            xRx = apoio["x"]

    
    if n_Ry == 2: # Caso isostático: 2 reações em y
        x_apoio=[]
        for apoio in apoios:
            if apoio["Ry"] == True: 
                x_apoio.append(apoio["x"]) #Pegando o ponto de cada apoio em y
        x_apoio.sort() #Para organizar a ordem dos apoios
        
        #Calculando a reação em y no apoio da direita calculando momento em A:
        By=-(np.sum(F_point*(r_point-x_apoio[0]))+
             np.sum(F_moment)+
             np.sum(F_distributed_res*(r_distributed_res-x_apoio[0])))/(x_apoio[1]-x_apoio[0])

        #Calculando a reação em y de apoio na esquerda calculando somatório de forças em y:
        Ay=-(np.sum(F_point)+np.sum(F_distributed_res)) - By

        print(f"A reação em y do primeiro apoio = {Ay:.2f} kN")
        
        print(f"A reação em y do segundo apoio = {By:.2f} kN")
        
        print(f"A reação em x do apoio de 2º gênero = {Rx:.2f} kN")

    
    if len(apoios)==1: #engaste
        #Calculando a reação de apoio de momento no engaste calculando o momento em A(no apoio):
        x_apoio = apoios[0]["x"]
        Mz=-(np.sum(F_point*(r_point-x_apoio))+
             np.sum(F_moment)+
             np.sum(F_distributed_res*(r_distributed_res-x_apoio)))

        #Calculando a reação em y do engaste somatório de forças em y:
        Ay=-(np.sum(F_point)+np.sum(F_distributed_res))
        
        print(f"A reação em y = {Ay:.2f} kN")
        
        print(f"A reação em x = {Rx:.2f} kN")
        
        print(f"A reação de momento = {Mz:.2f} kNm")

        
    #Calculo dos esforços:
    #Definindo um eixo global:
    n = int(1000 * L)
    eixo=np.linspace(0,L,n)
    eixo[-1] = L
    
    #Definindo uma lista com a carga em todos o domínio da viga
    q_total_y = np.zeros_like(eixo)
    q_total_x = np.zeros_like(eixo)
    
    #Contabilizando a contribuição das cargas distribuidas para a carga total na viga
    for load in dic:
        if load["type"] == "distributed":
            x1, x2 = load["x"]
            dx = (eixo >= x1) & (eixo <= x2)
            q = load["q"]
            if callable(q):
                q_total_y[dx] += q(eixo[dx])
            else:
                q_total_y[dx] += q
        
        if load["type"] == "distributed_x":
            x1, x2 = load["x"]
            dx = (eixo >= x1) & (eixo <= x2)
            q = load["q"]
            if callable(q):
                q_total_x[dx] += q(eixo[dx])
            else:
                q_total_x[dx] += q
    
    
    #Calculando o cortante através da integral da carga em y
    Q = -sc.cumulative_trapezoid(q_total_y, eixo, initial=0)

    #Calculando o normal através da integral da carga em x
    N = -sc.cumulative_trapezoid(q_total_x, eixo, initial=0)
    
    #Adicionando a contribuição das reações de apoio no cortante
    if len(apoios) == 1:
        Q[eixo >= x_apoio] += Ay

    if n_Ry == 2:
        Q[eixo >= x_apoio[0]] += Ay
        Q[eixo >= x_apoio[1]] += By

    #Adicionando a contribuição das reações de apoio no normal
    N[eixo >= xRx] += -Rx
  
    #Adicionando a contribuição das forças concentradas no cortante e no normal
    for load in dic:
        if load["type"] == "point":
            Q[eixo >= load["x"]] += load["value"]
        
        if load["type"] == "point_x":
            N[eixo >= load["x"]] += -load["value"]
    
    #Calculando o momento fletor a partir da integral do cortante
    M = sc.cumulative_trapezoid(Q, eixo, initial=0)

    #Adicionando a contribuição dos momentos concentrados das cargas ou do engaste no momento fletor:
    for load in dic:
        if load["type"] == "moment":
            M[eixo >= load["x"]] += -load["value"]

    if len(apoios) == 1:
        M[eixo >= x_apoio] += -Mz
        

    #Preparando os dados de normal, cortanate e momento para que eles partam do 0 mesmo quando há descontinuidade gerada por reação ou carga concentrada:
    eixo_plot=np.insert(eixo,0,0)
    N_plot=np.insert(N,0,0)
    Q_plot=np.insert(Q,0,0)
    M_plot=np.insert(M,0,0)

    #Construção dos gráficos:
    fig, axs = plt.subplots(3, 1, figsize=(6, 6), sharex=True)
    fig.subplots_adjust(hspace=0.8)

    axs[0].plot(eixo_plot, N_plot)
    axs[0].set_title("Diagrama dos Esforços Normais")
    axs[0].set_ylabel("N (kN)")
    axs[0].axhline(0, color="black", linewidth=1)
    axs[0].grid()

    axs[1].plot(eixo_plot, Q_plot)
    axs[1].set_title("Diagrama dos Esforços Cortantes")
    axs[1].set_ylabel("Q (kN)")
    axs[1].axhline(0, color="black", linewidth=1)
    axs[1].grid()

    axs[2].plot(eixo_plot, -M_plot)
    axs[2].set_title("Diagrama dos Momentos Fletores")
    axs[2].set_xlabel("x (m)")
    axs[2].set_ylabel("M (kNm)")
    axs[2].axhline(0, color="black", linewidth=1)
    axs[2].grid()
    return fig

st.title("Diagramas de Esforços em Vigas")

st.write("Modelo simples de viga isostática")

#Preparando as listas em que serão adicionados os apoios e os carregamentos

if "dic" not in st.session_state:
    st.session_state.dic = []

if "apoios" not in st.session_state:
    st.session_state.apoios = []

# Inputs
L = st.number_input("Comprimento da viga (m)", min_value=0.1, value=5.0)


st.subheader("Adicionar apoio")

x_apoio = st.number_input("Posição do apoio (m)", min_value=0.0, value=0.0)

tipo_apoio = st.selectbox(
    "Tipo de apoio",
    ["Rolete [Fy]", "Guia_horizontal[Fx]", "Pino[Fx,Fy]", "Engaste[Fx,Fy,Mz]"])

if st.button("Adicionar apoio"):
    if tipo_apoio == "Pino[Fx,Fy]":
        apoio = {"x": x_apoio, "Rx": True, "Ry": True, "Mz": False}
    elif tipo_apoio == "Guia_horizontal[Fx]":
        apoio = {"x": x_apoio, "Rx": True, "Ry": False, "Mz": False}
    elif tipo_apoio == "Rolete [Fy]":
        apoio = {"x": x_apoio, "Rx": False, "Ry": True, "Mz": False}
    elif tipo_apoio == "Engaste[Fx,Fy,Mz]":
        apoio = {"x": x_apoio, "Rx": True, "Ry": True, "Mz": True}

    st.session_state.apoios.append(apoio)

st.subheader("Apoios definidos")

for i, apoio in enumerate(st.session_state.apoios):
    st.write(
        f"Apoio {i+1} → x = {apoio['x']} m | "
        f"Rx = {apoio['Rx']} | Ry = {apoio['Ry']} | Mz = {apoio['Mz']}"
    )

if st.button("Limpar apoios"):
    st.session_state.apoios = []


st.subheader("Carregamentos na viga")
tipo_load = st.selectbox(
    "Tipo do carregamento",
    ["X pontual", "Y pontual", "Momento concentrado", "X distribuido", "Y distribuido"])

if tipo_load in ["X distribuido", "Y distribuido"]:

    col1, col2 = st.columns(2)

    with col1:
        x_ini = st.number_input(
            "x inicial (m)",
            min_value=0.0,
            key="x_ini"
        )

    with col2:
        x_fim = st.number_input(
            "x final (m)",
            min_value=x_ini,
            key="x_fim"
        )

    x_load = [x_ini, x_fim]
    
    expr = st.text_input(
        "Função da carga q(x)",
        value="30*x",
        help="Exemplos: 10 | 30*x | 5 + 2*x | 20*sin(x)")   

elif tipo_load in ["X pontual", "Y pontual"]:
    x_load = st.number_input(
        "Onde será aplicado o carregamento (m)",
        min_value=0.0,
        key="x_pontual")
    valor = st.number_input("Valor da força concentrada(kN))")  

elif tipo_load == "Momento concentrado":
    x_load = st.number_input(
        "Onde será aplicado o carregamento (m)",
        min_value=0.0,
        key="x_pontual")
    valor = st.number_input("Valor do momento concentrado(kNm)")

if st.button("Adicionar carregamento"):
    
    if tipo_load == "Y pontual":
        load = {"type": "point",
                "x": x_load,
                "value": valor}

    elif tipo_load == "Momento concentrado":
        load = {"type": "moment",
                "x": x_load,
                "value": valor}

    elif tipo_load == "X pontual":
        load = {"type": "point_x",
                "x": x_load,
                "value": valor}
        
    elif tipo_load == "Y distribuido":
        q_func = criar_funcao_distribuida(expr)

        # teste rápido de validade
        q_func(np.array([x_ini, x_fim]))

        load = {"type": "distributed",
                "x": [x_ini, x_fim],
                "q": q_func}

    elif tipo_load == "X distribuido":
        q_func = criar_funcao_distribuida(expr)

        q_func(np.array([x_ini, x_fim]))

        load = {"type": "distributed_x",
                "x": [x_ini, x_fim],
                "q": q_func}
    st.session_state.dic.append(load)

st.subheader("Carregamentos adicionados")

for i, load in enumerate(st.session_state.dic):
    st.write(f"Carregamento {i+1} → x = {load}")

if st.button("Limpar carregamentos"):
    st.session_state.dic = []

#Adptando returns para o streamlit:
def rodar_viga_streamlit(dic, L, apoios):
    buffer = io.StringIO()

    try:
        with contextlib.redirect_stdout(buffer):
            resultado = diagramas_viga(dic, L, apoios)

        logs = buffer.getvalue()

        if isinstance(resultado, str):
            return {"status": "erro", "mensagem": resultado, "logs": logs}

        return {"status": "ok", "fig": resultado, "logs": logs}

    except Exception as e:
        return {"status": "erro", "mensagem": str(e), "logs": buffer.getvalue()}
    
#Preparando o resultado:
if st.button("Calcular"):
    saida = []
    saida = rodar_viga_streamlit(st.session_state.dic, L, st.session_state.apoios)

    if saida["logs"]:
        st.subheader("📋 Resultados")
        st.text(saida["logs"])

    if saida["status"] == "erro":
        st.error(saida["mensagem"])
        st.stop()


    st.pyplot(saida["fig"])
