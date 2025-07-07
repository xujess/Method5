import streamlit as st
import pandas as pd
import numpy as np
import random
import statistics
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import plotly.express as px


# 自定义标价，可以录入多个，用逗号隔开
bids = []

st.title("方法五:ABC合成法")
st.header("1. 输入所有有效投标报价")
input_bids = st.text_input("用逗号分隔开，可录入多个")

if input_bids:
  bids += input_bids.split(",")
  bids = [float(bid) for bid in bids]
  bids.sort(reverse=True)

if bids:
    # Create a DataFrame for display with a 1-based index
    bids_df = pd.DataFrame({
        '序号': range(1, len(bids) + 1),
        '投标报价': bids
    })
    st.dataframe(bids_df.set_index('序号'))
  
st.header("2. 调整参数")


# 设置默认的 deltas 和 Ks
default_deltas = [0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.2]
default_Ks = [0.95, 0.955, 0.96, 0.965, 0.97, 0.975, 0.98]

# 用户自定义 deltas 和 Ks 输入
input_deltas = st.text_input("录入下浮率Δ，用逗号分隔开：", value=','.join(map(str, default_deltas)))
input_Ks = st.text_input("录入下浮系数K，用逗号分隔开：", value=','.join(map(str, default_Ks)))

# 转换用户输入为浮点数列表，如果转换失败则使用默认值
try:
    deltas = [float(delta.strip()) for delta in input_deltas.split(",")]
    Ks = [float(K.strip()) for K in input_Ks.split(",")]
except ValueError:
    st.error("下浮率Δ和下浮系数K必须是由逗号分隔的数字。")
    deltas = default_deltas
    Ks = default_Ks

# Use columns to place the number inputs side-by-side
col1, col2, col3, col4 = st.columns(4)

with col1:
    wA_percent = st.number_input("A的权重 (%)", min_value=0, max_value=100, value=50, step=1)

with col2:
    wB_percent = st.number_input("B的权重 (%)", min_value=0, max_value=100, value=30, step=1)

# Validate that the sum of A and B is not more than 100
if wA_percent + wB_percent > 100:
    st.error("错误：A和B的权重之和不能超过100%。")
    st.stop() # Stop the app from running further until the error is fixed.

# Calculate C's weight automatically and display it
wC_percent = 100 - wA_percent - wB_percent
with col3:
    st.number_input("C的权重 (%) (自动计算)", value=wC_percent, disabled=True)

with col4:
    lower_rate_percent = st.number_input("规定范围下浮率 (%)", min_value=0, max_value=100, value=25, step=1)
  
# Convert percentage weights to decimal form for calculations
wA = wA_percent / 100.0
wB = wB_percent / 100.0
wC = wC_percent / 100.0
lower_rate_decimal = lower_rate_percent / 100.0


# 设置参数
control_price = 1

# 计算C值
# 计算评标价平均值 和范围下限

if bids:  # 确保 bids 不为空
  bid_mean = statistics.mean(bids)
  lower_limit = (bid_mean * 0.7 + control_price * 0.3) * (1 - lower_rate_decimal)

  # 过滤bids,得到在范围内的bids
  in_range_bids = [b for b in bids if b >= lower_limit]

  # 如果 in_range_bids 不为空，继续计算
  if in_range_bids:

    # C=在规定范围内的最低评标价
    in_range_bids.sort()
    C = in_range_bids[0]

    data = []
    for delta in deltas:

      # A=招标控制价×（100%－下浮率Δ）
      A = control_price * (1-delta)
      A = round(A,2)

      # B_range为0.95A到C之间
      B_range = [b for b in bids if C < b < A*0.95]

      # 如果B_range为空，则使用除C外的任何有效报价作为新的B_range
      if not B_range:
          B_range = [b for b in in_range_bids if b != C]

      for b in B_range:
        # Use the dynamic weights from the number inputs in the calculation
        weighted_sum = wA*A + wB*b + wC*C
        weighted_sum = round(weighted_sum,6)

        for K in Ks:
          benchmark = weighted_sum * K
          benchmark = round(benchmark,6)
          data.append([delta,A,round(0.95*A,6),round(bid_mean,6),round(lower_limit,6),C,b,weighted_sum,K,benchmark])

    df = pd.DataFrame(data, columns=[
      '下浮率Δ', 'A', '0.95*A', '报价平均值','规定范围内', 'C', 'B',
      '加权平均值', '系数K', '评标基准价'])


    # The title now displays integer percentages
    st.title(f"评标基准价=(A×{wA_percent}%＋B×{wB_percent}%＋C×{wC_percent}%)×K")

    # MODIFIED: Added this markdown block to explain the variables.
    st.markdown(f"""
    <small>其中:</small>
    <ul>
      <li><b>A</b> = 招标控制价 × (1 - 下浮率Δ)</li>
      <li><b>C</b> = 规定范围内的最低评标价 (规定范围内:评标价算术平均值×70%与招标控制价×30%之和下浮{lower_rate_percent}%以内的所有评标价)</li>
      <li><b>B</b> = 在 C 与 0.95×A 之间的任一有效投标报价(若该范围无报价，则B为除C外的任一有效报价)</li>
    </ul>
    """, unsafe_allow_html=True)

    
    # 计算箱线图的统计数据
    # Check if DataFrame is empty before proceeding
    if not df.empty:
        # MODIFIED: Create a container to hold the charts. This allows us to define the slider
        # after the container in the code, so it appears below the charts on the page.
        chart_container = st.container()
        
        # MODIFIED: Define the slider here, after the chart container.
        bins = st.slider('调整直方图的bin数量:', min_value=1, max_value=len(df['评标基准价']), value=30)

        stats = df['评标基准价'].describe(percentiles=[.25, .5, .75])
        min_val = stats['min']
        q1_val = stats['25%']
        median_val = stats['50%']
        q3_val = stats['75%']
        max_val = stats['max']

        # 设置刻度值和刻度标签，保留小数点六位
        tickvals = [min_val, q1_val, median_val, q3_val, max_val]
        ticktext = [f"{min_val:.6f}", f"{q1_val:.6f}", f"{median_val:.6f}", f"{q3_val:.6f}", f"{max_val:.6f}"]

        # 创建箱线图
        fig_box = px.box(df, y='评标基准价', points="all")
        fig_box.update_traces(marker=dict(size=3))
        fig_box.update_layout(
            autosize=True,
            yaxis=dict(tickvals=tickvals, ticktext=ticktext)
        )
        fig_box.update_yaxes(title='评标基准价')

        # 创建水平直方图并根据滑块的值调整bin的数量
        fig_hist = px.histogram(df, y='评标基准价', orientation='h', nbins=bins)
        fig_hist.update_layout(
            bargap=0.1,
            yaxis=dict(tickvals=tickvals, ticktext=ticktext)
        )
        fig_hist.update_xaxes(title='数量')
        
        # MODIFIED: Fill the container with the charts
        with chart_container:
            # 用 Streamlit 的 columns 创建两列并排显示图表
            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                st.plotly_chart(fig_box, use_container_width=True)
            with chart_col2:
                st.plotly_chart(fig_hist, use_container_width=True)

        
        st.subheader("详细数据表")
      
        df.index = pd.RangeIndex(start=1, stop=len(df) + 1, name='序号')
        st.dataframe(df) # Using st.dataframe for better interactivity
    else:
        st.warning("没有生成有效数据。请检查输入的投标报价和参数设置。")
