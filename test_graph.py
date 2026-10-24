
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Graph Test")

st.title("Graph Display Test")

graph = """
<svg xmlns="http://www.w3.org/2000/svg"
     width="700" height="350"
     viewBox="0 0 700 350">

<rect width="700" height="350" fill="white"/>

<text x="180" y="35"
      font-size="22" fill="black">
Electricity Forecast Test
</text>

<line x1="60" y1="290"
      x2="650" y2="290"
      stroke="black" stroke-width="2"/>

<line x1="60" y1="60"
      x2="60" y2="290"
      stroke="black" stroke-width="2"/>

<polyline
    points="60,250 160,210 260,230 360,130 460,160 560,90 650,120"
    fill="none"
    stroke="blue"
    stroke-width="4"/>

</svg>
"""

components.html(graph, height=370, scrolling=False)

st.success("Graph test completed!")
