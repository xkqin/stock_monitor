import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import pytz

def get_stock_data(symbol, period="1d", interval="1m"):
    """获取股票数据用于K线图"""
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=period, interval=interval)
        if not df.empty:
            return df
        return None
    except Exception as e:
        st.error(f"获取{symbol}K线数据失败: {str(e)}")
        return None

def get_stock_info(symbol):
    """获取股票实时信息"""
    try:
        # 获取实时数据
        stock = yf.Ticker(symbol)
        
        # 获取当前交易日数据
        today_data = stock.history(period='1d')
        if len(today_data) > 0:
            # 使用 iloc[0] 来获取标量值
            current_price = float(today_data['Close'].iloc[-1])
            prev_close = float(stock.info.get('previousClose', current_price))
            volume = int(today_data['Volume'].iloc[-1])
            market_cap = float(stock.info.get('marketCap', 0))
            
            return {
                'price': current_price,
                'prev_close': prev_close,
                'volume': volume,
                'market_cap': market_cap
            }
    except Exception as e:
        st.error(f"Failed to get {symbol} data: {str(e)}")
    return None

def format_number(number):
    """格式化大数字显示"""
    try:
        if number >= 1_000_000_000:
            return f"{number/1_000_000_000:.2f}B"
        elif number >= 1_000_000:
            return f"{number/1_000_000:.2f}M"
        elif number >= 1_000:
            return f"{number/1_000:.2f}K"
        return f"{number:.2f}"
    except:
        return "N/A"

def get_ma_comparison(symbol):
    """获取股票当前价格与20日均线的差值比较"""
    try:
        df = yf.download(symbol, period="1mo", interval="1d", progress=False)
        if not df.empty and len(df) >= 20:
            current_price = float(df['Close'].iloc[-1])
            ma_series = df['Close'].rolling(window=20).mean()
            ma20 = float(ma_series.iloc[-1])
            diff_percent = ((current_price - ma20) / ma20) * 100
            return {
                'ma20': ma20,
                'diff_percent': diff_percent
            }
        else:
            st.warning(f"{symbol} 数据不足以计算20日均线")
    except Exception as e:
        st.error(f"Failed to get {symbol} MA data: {str(e)}")
    return None

def get_market_status():
    """获取美股市场状态"""
    now = datetime.now(pytz.timezone('America/New_York'))  # 使用纽约时区
    
    # 判断是否为周末
    if now.weekday() >= 5:  # 5是周六，6是周日
        return "🔴 休市中"
    
    # 判断是否在交易时间内 (9:30 AM - 4:00 PM ET)
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    if market_open <= now <= market_close:
        return "🟢 交易中"
    else:
        return "🔴 休市中"

def main():
    st.title("纳斯达克七姐妹实时监控")
    
    magnificent_seven = {
        'MSFT': 'Microsoft 微软',
        'AAPL': 'Apple 苹果',
        'GOOGL': 'Google-A 谷歌',
        'NVDA': 'NVIDIA 英伟达',
        'AMZN': 'Amazon 亚马逊',
        'META': 'Meta 元宇宙',
        'TSLA': 'Tesla 特斯拉'
    }

    # 使用纽约时区显示市场状态和更新时间
    ny_time = datetime.now(pytz.timezone('America/New_York'))
    market_status = get_market_status()
    
    st.sidebar.write(f"市场状态: {market_status}")

    # 添加数据时间范围选择
    time_range = st.sidebar.selectbox(
        "K线图时间范围",
        [
            ("1天", "1d", "1m"),
            ("5天", "5d", "5m"),
            ("1月", "1mo", "1h"),
            ("3月", "3mo", "1d"),
            ("1年", "1y", "1d")
        ],
        format_func=lambda x: x[0]
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("纳斯达克综合指数")
        with st.spinner("加载纳斯达克数据..."):
            nasdaq_data = get_stock_data("^IXIC", period=time_range[1], interval=time_range[2])
            
            if nasdaq_data is not None and not nasdaq_data.empty:
                fig = go.Figure()
                
                # 添加K线图
                fig.add_trace(go.Candlestick(
                    x=nasdaq_data.index,
                    open=nasdaq_data['Open'],
                    high=nasdaq_data['High'],
                    low=nasdaq_data['Low'],
                    close=nasdaq_data['Close'],
                    name='NASDAQ'
                ))
                
                # 计算并添加均线
                for period in [5, 10, 20]:
                    if len(nasdaq_data) > period:
                        ma = nasdaq_data['Close'].rolling(window=period).mean()
                        fig.add_trace(go.Scatter(
                            x=nasdaq_data.index,
                            y=ma,
                            name=f'{period}日均线',
                            line=dict(width=1)
                        ))
                
                fig.update_layout(
                    height=500,
                    title="纳斯达克走势",
                    yaxis_title="价格",
                    xaxis_title="时间",
                    template="plotly_dark"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("无法获取纳斯达克数据")

    with col2:
        st.subheader("七姐妹实时数据")
        
        # 七姐妹数据 - 使用更紧凑的列表形式
        st.markdown("""
            <div style="
                margin-top: 20px;
                padding: 15px;
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
            ">
            <div style="
                font-size: 1em;
                color: #888;
                margin-bottom: 10px;
            ">七姐妹实时数据</div>
            """, 
            unsafe_allow_html=True
        )
        
        # 创建3列布局
        cols = st.columns(3)
        
        # 遍历显示七姐妹数据
        for i, (symbol, name) in enumerate(magnificent_seven.items()):
            with cols[i % 3]:
                st.markdown(
                    f"""
                    <div style="
                        border: 1px solid #444;
                        border-radius: 6px;
                        padding: 8px;
                        margin: 4px 0;
                        background-color: rgba(255, 255, 255, 0.02);
                        font-family: monospace;
                    ">
                        <div style="text-align: center; color: #888; margin-bottom: 5px;">
                            {symbol}
                        </div>
                        <div style="text-align: center; margin: 5px 0; font-size: 1.1em;">
                    """,
                    unsafe_allow_html=True
                )
                
                with st.spinner(f"Loading {symbol}..."):
                    data = get_stock_info(symbol)
                    ma_data = get_ma_comparison(symbol)
                    
                    if data and ma_data:
                        current_price = data['price']
                        prev_close = data['prev_close']
                        change_percent = ((current_price - prev_close) / prev_close) * 100
                        ma20 = ma_data['ma20']
                        diff_percent = ma_data['diff_percent']
                        
                        price_color = '#00FF00' if change_percent >= 0 else '#FF4444'
                        ma_color = '#00FF00' if diff_percent >= 0 else '#FF4444'
                        
                        st.markdown(
                            f"""
                                <span>${current_price:.3f}</span>
                                <span style="color: {price_color}; margin-left: 8px;">
                                    {change_percent:+.2f}%
                                </span>
                            </div>
                            <div style="text-align: center; color: #888; margin-top: 8px;">
                                MA20: ${ma20:.3f}
                            </div>
                            <div style="text-align: center; margin-top: 4px; color: #888;">
                                均线差: <span style="color: {ma_color};">
                                    {diff_percent:+.2f}%
                                </span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            """
                                <span>No data</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    # 刷新控制
    col3, col4 = st.columns(2)
    with col3:
        refresh_interval = st.selectbox(
            "刷新间隔",
            [("不自动刷新", 0), ("30秒", 30), ("1分钟", 60), ("5分钟", 300)],
            format_func=lambda x: x[0]
        )
    with col4:
        if st.button("立即刷新"):
            st.rerun()

    # 显示最后更新时间（纽约时间）
    st.markdown(f"*最后更新时间: {ny_time.strftime('%Y-%m-%d %H:%M:%S')} ET*")

    # 自动刷新
    if refresh_interval[1] > 0:
        time.sleep(refresh_interval[1])
        st.rerun()

if __name__ == "__main__":
    main() 