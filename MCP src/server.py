"""MCP server entry for the lightning fault diagnosis tool."""

from __future__ import annotations

import base64
import logging

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, ImageContent, TextContent

from client import APIClient, APIClientError, DataNotFoundError
from diagnosis_engine import _parse_date, build_report

# Route library logs to stderr and keep stdout clean for MCP stdio transport.
logging.basicConfig(level=logging.WARNING, handlers=[logging.StreamHandler()])
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)

mcp = FastMCP("lightning-diagnosis")


@mcp.tool()
async def diagnose_lightning_tool(query_date: str, line_name: str) -> CallToolResult:
    """基于日期和线路名查询雷击故障诊断结果。

    Args:
        query_date: 查询日期，支持 "2025-05-08" 或 "2025年5月8日"。
        line_name: 线路名称，如 "雅湖线"，需与 getTripInfoData 返回的 tripLineName 精确匹配。

    Returns:
        CallToolResult，content[0] 为 Markdown 诊断报告，content[1..3] 为三张故障波形图。
    """
    client = APIClient()
    try:
        iso_date = _parse_date(query_date)
        trip_id = await client.get_trip_info_data(iso_date, line_name)
        diagnosis, info, ripple, weather = await client.fetch_all_diagnosis_data(trip_id)
        report = build_report(diagnosis, info, ripple, weather)

        content: list[TextContent | ImageContent] = [
            TextContent(type="text", text=report["markdown"])
        ]
        for image_bytes in report["images"]:
            content.append(
                ImageContent(
                    type="image",
                    data=base64.b64encode(image_bytes).decode("utf-8"),
                    mimeType="image/png",
                )
            )

        return CallToolResult(content=content, isError=False)
    except DataNotFoundError as exc:
        return CallToolResult(
            content=[TextContent(type="text", text=exc.message)],
            isError=True,
        )
    except APIClientError as exc:
        return CallToolResult(
            content=[TextContent(type="text", text=exc.message)],
            isError=True,
        )
    except Exception as exc:
        return CallToolResult(
            content=[TextContent(type="text", text=f"诊断过程中发生未知错误: {exc}")],
            isError=True,
        )
    finally:
        await client.close()


if __name__ == "__main__":
    mcp.run(transport="stdio")
