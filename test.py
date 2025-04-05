import plotly
import plotly.express as px
import plotly.io as pio
pio.kaleido.scope.default_format = "png"
pio.kaleido.scope.default_width = 800
pio.kaleido.scope.default_height = 600

print("Plotly version:", plotly.__version__)

fig = px.line(x=[1, 2, 3], y=[1, 4, 9])
# fig.write_image("test_plot.png", engine="kaleido")
fig.write_image("test_plot.png")
print("Saved successfully ✅")