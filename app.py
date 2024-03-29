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

st.title("方法五自定义标价")

input_bids = st.text_input("用逗号分隔开，可录入多个")

if input_bids:
  bids += input_bids.split(",")
  bids = [float(bid) for bid in bids]

st.write(bids)


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


# 设置参数
control_price = 1

# 计算C值
# 计算评标价平均值 和范围下限

if bids:  # 确保 bids 不为空
  bid_mean = statistics.mean(bids)
  lower_limit = (bid_mean * 0.7 + control_price * 0.3) * 0.75

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
        weighted_sum = 0.5*A + 0.3*b + 0.2*C
        weighted_sum = round(weighted_sum,6)

        for K in Ks:
          benchmark = weighted_sum * K
          benchmark = round(benchmark,6)
          data.append([delta,A,round(0.95*A,6),C,b,weighted_sum,K,benchmark])

    df = pd.DataFrame(data, columns=[
      'delta', 'A', '0.95A', 'C', 'B',
      'weighted_sum', 'K', 'benchmark'])


    st.title("评标基准价=(A×50%＋B×30%＋C×20%)×K")


    # 计算箱线图的统计数据
    stats = df['benchmark'].describe(percentiles=[.25, .5, .75])
    min_val = stats['min']
    q1_val = stats['25%']
    median_val = stats['50%']
    q3_val = stats['75%']
    max_val = stats['max']

    # 设置刻度值和刻度标签，保留小数点六位
    tickvals = [min_val, q1_val, median_val, q3_val, max_val]
    ticktext = [f"{min_val:.6f}", f"{q1_val:.6f}", f"{median_val:.6f}", f"{q3_val:.6f}", f"{max_val:.6f}"]

    # 在图表上方添加滑块以调整直方图的bin数量
    bins = st.slider('调整直方图的bin数量:', min_value=1, max_value=len(df['benchmark']), value=30)

    # 创建箱线图
    fig_box = px.box(df, y='benchmark', points="all")
    fig_box.update_traces(marker=dict(size=3))  # 调整散点大小
    fig_box.update_layout(
        autosize=True,
        yaxis=dict(
            tickvals=tickvals,
            ticktext=ticktext
        )
    )
    fig_box.update_yaxes(title='Benchmark')


    # 创建水平直方图并根据滑块的值调整bin的数量
    fig_hist = px.histogram(df, y='benchmark', orientation='h', nbins=bins)
    fig_hist.update_layout(
        bargap=0.1,
        yaxis=dict(
            tickvals=tickvals,
            ticktext=ticktext
        )
    )
    fig_hist.update_xaxes(title='Count')

    # 用 Streamlit 的 columns 创建两列并排显示图表
    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(fig_box, use_container_width=True)

    with col2:
        st.plotly_chart(fig_hist, use_container_width=True)

    st.table(df)
