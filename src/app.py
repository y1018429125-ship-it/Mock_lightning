"""FastAPI application entry with custom Swagger UI and dynamic token defaults."""

import importlib
import pkgutil

from fastapi import Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

import token_manager
from main_app import app

# ---------------------------------------------------------------------------
# Static files: serve surveillance images
# ---------------------------------------------------------------------------
app.mount("/images", StaticFiles(directory="/Users/yfzx/Desktop/特高压/可视化监拍图片"), name="images")

# ---------------------------------------------------------------------------
# Custom OpenAPI: dynamically inject current token into schema defaults
# ---------------------------------------------------------------------------

def custom_openapi():
    openapi_schema = get_openapi(
        title="特高压线路故障诊断 API Mock 测试平台",
        version="1.0.0",
        routes=app.routes,
    )
    current_token = token_manager.get_token() or ""

    def _update_schema(schema):
        """Update access_token default in a schema dict."""
        props = schema.get("properties", {})
        if "access_token" in props:
            props["access_token"]["default"] = current_token

    # Handle both inline schemas and $ref schemas
    schemas = openapi_schema.get("components", {}).get("schemas", {})
    for schema in schemas.values():
        _update_schema(schema)

    # Also handle inline schemas in requestBody (for non-$ref cases)
    for path_data in openapi_schema.get("paths", {}).values():
        for operation in path_data.values():
            request_body = operation.get("requestBody", {})
            for media_type in request_body.get("content", {}).values():
                schema = media_type.get("schema", {})
                _update_schema(schema)

    return openapi_schema


app.openapi = custom_openapi

# ---------------------------------------------------------------------------
# Custom Swagger UI: auto-refresh page after successful login
# ---------------------------------------------------------------------------

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    response = get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=app.title,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )
    # FastAPI 0.115+ returns HTMLResponse object, not a string
    html = response.body.decode("utf-8")
    custom_js = """
    <script>
    // -------------------------------------------------------------------------
    // 统一 fetch 拦截：登录刷新 + getTripRipple 波形数据捕获
    // -------------------------------------------------------------------------
    var _tripRippleData = null;

    const _origFetch = window.fetch;
    window.fetch = async function(...args) {
        const response = await _origFetch.apply(this, args);
        var url = '';
        if (typeof args[0] === 'string') {
            url = args[0];
        } else if (args[0] && typeof args[0] === 'object' && args[0].url) {
            url = args[0].url;
        }

        // 登录成功后自动刷新页面
        if (url.includes('/userservice/login')) {
            const clone = response.clone();
            try {
                const data = await clone.json();
                if (data.code === 1001) {
                    setTimeout(() => location.reload(), 500);
                }
            } catch (e) {}
        }

        // 捕获 getTripRipple 响应数据
        if (url.includes('/lineflashtripservice/getTripRipple')) {
            const clone = response.clone();
            try {
                const data = await clone.json();
                if (data.code === 1001 && data.data) {
                    _tripRippleData = data.data;
                }
            } catch (e) {}
        }

        return response;
    };

    // 清理 Swagger UI 显示的 curl 命令：移除 -H 参数，与 txt 格式一致
    // Swagger UI 5.x 使用 microlight 类高亮代码，需匹配多种选择器
    function cleanCurl() {
        var selectors = ['pre.microlight', '.curl-command', '.curl', '[class*="curl"]', 'pre', 'code'];
        selectors.forEach(function(selector) {
            document.querySelectorAll(selector).forEach(function(el) {
                var text = el.textContent || '';
                if (!text.includes('curl') || !text.includes('-H')) return;
                var lines = text.split('\\n').filter(function(line) {
                    return !line.trim().startsWith('-H');
                });
                if (lines.length < text.split('\\n').length) {
                    el.textContent = lines.join('\\n');
                }
            });
        });
    }

    // MutationObserver 监听 DOM 变化，curl 出现时自动清理 + 波形图绘制
    var _mainObserver = new MutationObserver(function() {
        cleanCurl();
        drawWaveCharts();
    });
    _mainObserver.observe(document.body, { childList: true, subtree: true });

    // 高频兜底：每 50ms 检查一次，确保页面加载和切换时及时清理
    function pollClean() {
        cleanCurl();
        drawWaveCharts();
        setTimeout(pollClean, 50);
    }
    pollClean();

    function drawWaveCharts() {
        if (!_tripRippleData) return;
        // 只在 getTripRipple 响应区域绘制
        var opblocks = document.querySelectorAll('.opblock');
        opblocks.forEach(function(op) {
            if (!op.textContent.includes('getTripRipple')) return;
            var respBody = op.querySelector('.responses-inner, .response-col_description, .microlight');
            if (!respBody) return;
            // 如果已绘制，跳过
            if (op.querySelector('.wave-chart-container')) return;

            var container = document.createElement('div');
            container.className = 'wave-chart-container';
            container.style.marginTop = '20px';
            container.style.padding = '10px';
            container.style.background = '#fafafa';
            container.style.border = '1px solid #e0e0e0';
            container.style.borderRadius = '4px';

            var waveIndex = 0;
            for (var key in _tripRippleData) {
                if (!_tripRippleData.hasOwnProperty(key)) continue;
                var wave = _tripRippleData[key];
                if (!wave || !wave.items) continue;

                var title = document.createElement('div');
                title.textContent = '故障波形：' + (wave.waveType || '') + '波形';
                title.style.fontWeight = 'bold';
                title.style.marginBottom = '8px';
                title.style.fontSize = '14px';
                container.appendChild(title);

                var svg = createWaveSvg(wave.items, wave.waveType || ('波形' + (waveIndex + 1)), waveIndex);
                container.appendChild(svg);

                var spacer = document.createElement('div');
                spacer.style.height = '20px';
                container.appendChild(spacer);

                waveIndex++;
            }

            respBody.parentNode.insertBefore(container, respBody.nextSibling);
        });
    }

    function createWaveSvg(items, waveType, waveIndex) {
        var W = 600, H = 280, PAD = {top: 20, right: 20, bottom: 40, left: 50};
        var GW = W - PAD.left - PAD.right;
        var GH = H - PAD.top - PAD.bottom;

        // 采样：避免过多数据点挤在一起（每个像素最多一个点）
        var step = Math.max(1, Math.ceil(items.length / GW));
        var sampled = [];
        for (var i = 0; i < items.length; i += step) {
            sampled.push(items[i]);
        }
        if (sampled[sampled.length - 1] !== items[items.length - 1]) {
            sampled.push(items[items.length - 1]);
        }
        items = sampled;

        var xs = items.map(function(p) { return p.x; });
        var ys = items.map(function(p) { return p.y; });
        var minX = Math.min.apply(null, xs);
        var maxX = Math.max.apply(null, xs);
        var minY = Math.min.apply(null, ys);
        var maxY = Math.max.apply(null, ys);

        // 固定坐标轴范围
        var isGongpin = (waveType === '工频');
        var isHangbo = (waveType === '行波');
        if (isGongpin) {
            minX = 0; maxX = 1200;
            minY = -2000; maxY = 5000;
        } else if (isHangbo && waveIndex === 0) {
            // 第一个行波
            minX = 0; maxX = 7000;
            minY = -2000; maxY = 1000;
        } else if (isHangbo && waveIndex === 1) {
            // 第二个行波
            minX = 0; maxX = 7000;
            minY = -3000; maxY = 2000;
        } else {
            if (minY === maxY) { minY -= 1; maxY += 1; }
            if (minX === maxX) { minX -= 1; maxX += 1; }
        }

        var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', W);
        svg.setAttribute('height', H);
        svg.style.display = 'block';
        svg.style.marginBottom = '10px';

        // 背景
        var rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('width', W);
        rect.setAttribute('height', H);
        rect.setAttribute('fill', 'white');
        svg.appendChild(rect);

        // 网格线
        var gridGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        var yTicks, xTicks;
        if (isGongpin) {
            yTicks = [-2000, -1000, 0, 1000, 2000, 3000, 4000, 5000];
            xTicks = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200];
        } else if (isHangbo && waveIndex === 0) {
            // 第一个行波
            yTicks = [-2000, -1500, -1000, -500, 0, 500, 1000];
            xTicks = [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000];
        } else if (isHangbo && waveIndex === 1) {
            // 第二个行波
            yTicks = [-3000, -2000, -1000, 0, 1000, 2000];
            xTicks = [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000];
        } else {
            yTicks = [];
            for (var i = 0; i <= 5; i++) yTicks.push(minY + (maxY - minY) * i / 5);
            xTicks = [];
            for (var i = 0; i <= 5; i++) xTicks.push(minX + (maxX - minX) * i / 5);
        }

        yTicks.forEach(function(tv) {
            var y = PAD.top + GH - GH * (tv - minY) / (maxY - minY);
            var line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', PAD.left);
            line.setAttribute('y1', y);
            line.setAttribute('x2', PAD.left + GW);
            line.setAttribute('y2', y);
            line.setAttribute('stroke', '#e0e0e0');
            line.setAttribute('stroke-width', '1');
            gridGroup.appendChild(line);
        });
        xTicks.forEach(function(tv) {
            var x = PAD.left + GW * (tv - minX) / (maxX - minX);
            var line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', x);
            line.setAttribute('y1', PAD.top);
            line.setAttribute('x2', x);
            line.setAttribute('y2', PAD.top + GH);
            line.setAttribute('stroke', '#e0e0e0');
            line.setAttribute('stroke-width', '1');
            gridGroup.appendChild(line);
        });
        svg.appendChild(gridGroup);

        // 坐标轴 + 刻度标签
        var axisGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        var xAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        xAxis.setAttribute('x1', PAD.left);
        xAxis.setAttribute('y1', PAD.top + GH);
        xAxis.setAttribute('x2', PAD.left + GW);
        xAxis.setAttribute('y2', PAD.top + GH);
        xAxis.setAttribute('stroke', '#333');
        xAxis.setAttribute('stroke-width', '2');
        axisGroup.appendChild(xAxis);

        var yAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        yAxis.setAttribute('x1', PAD.left);
        yAxis.setAttribute('y1', PAD.top);
        yAxis.setAttribute('x2', PAD.left);
        yAxis.setAttribute('y2', PAD.top + GH);
        yAxis.setAttribute('stroke', '#333');
        yAxis.setAttribute('stroke-width', '2');
        axisGroup.appendChild(yAxis);

        // 刻度数值标签
        function fmtNum(v) {
            if (Math.abs(v) >= 1000) return v.toFixed(0);
            if (Math.abs(v) >= 1) return v.toFixed(1);
            return v.toFixed(3);
        }

        // X轴刻度值
        xTicks.forEach(function(tv) {
            var tx = PAD.left + GW * (tv - minX) / (maxX - minX);
            var tick = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            tick.setAttribute('x', tx);
            tick.setAttribute('y', PAD.top + GH + 14);
            tick.setAttribute('text-anchor', 'middle');
            tick.setAttribute('font-size', '10');
            tick.setAttribute('fill', '#666');
            tick.textContent = fmtNum(tv);
            axisGroup.appendChild(tick);
        });

        // Y轴刻度值
        yTicks.forEach(function(tv) {
            var ty = PAD.top + GH - GH * (tv - minY) / (maxY - minY);
            var tick = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            tick.setAttribute('x', PAD.left - 6);
            tick.setAttribute('y', ty + 3);
            tick.setAttribute('text-anchor', 'end');
            tick.setAttribute('font-size', '10');
            tick.setAttribute('fill', '#666');
            tick.textContent = fmtNum(tv);
            axisGroup.appendChild(tick);
        });

        svg.appendChild(axisGroup);

        // 波形线
        var pathData = '';
        for (var i = 0; i < items.length; i++) {
            var px = PAD.left + GW * (items[i].x - minX) / (maxX - minX);
            var py = PAD.top + GH - GH * (items[i].y - minY) / (maxY - minY);
            pathData += (i === 0 ? 'M' : 'L') + px + ' ' + py;
        }
        var path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', pathData);
        path.setAttribute('stroke', '#2196F3');
        path.setAttribute('stroke-width', '1.5');
        path.setAttribute('fill', 'none');
        svg.appendChild(path);

        // X轴标签
        var xLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        xLabel.setAttribute('x', PAD.left + GW / 2);
        xLabel.setAttribute('y', H - 8);
        xLabel.setAttribute('text-anchor', 'middle');
        xLabel.setAttribute('font-size', '12');
        xLabel.setAttribute('fill', '#555');
        var xUnit = (waveType === '工频') ? '毫秒' : '微秒';
        xLabel.textContent = '时间（' + xUnit + '）';
        svg.appendChild(xLabel);

        // Y轴标签
        var yLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        yLabel.setAttribute('x', 15);
        yLabel.setAttribute('y', PAD.top + GH / 2);
        yLabel.setAttribute('text-anchor', 'middle');
        yLabel.setAttribute('font-size', '12');
        yLabel.setAttribute('fill', '#555');
        yLabel.setAttribute('transform', 'rotate(-90, 15, ' + (PAD.top + GH / 2) + ')');
        yLabel.textContent = '电流（安培）';
        svg.appendChild(yLabel);

        return svg;
    }

    </script>
    """
    return HTMLResponse(html.replace("</body>", custom_js + "</body>"))

# ---------------------------------------------------------------------------
# Auto-import all generated API modules
# ---------------------------------------------------------------------------

import generated

for _, name, _ in pkgutil.iter_modules(generated.__path__):
    if name.endswith("_api"):
        importlib.import_module(f"generated.{name}")

print(f"Loaded {len([n for _, n, _ in pkgutil.iter_modules(generated.__path__) if n.endswith('_api')])} API modules")
