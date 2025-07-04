import os
import re
import json
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# 确保下载目录存在
DOWNLOADS_DIR = "downloads"
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

app = FastAPI(title="Douyin Video Downloader API")

# 请求头，模拟移动端访问
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/121.0.2277.107 Version/17.0 Mobile/15E148 Safari/604.1'
}

# 定义接收请求的数据模型
class VideoRequest(BaseModel):
    url: str

def parse_douyin_share_url(share_text: str) -> dict:
    """从分享文本中提取无水印视频链接"""
    # 提取分享链接
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', share_text)
    if not urls:
        raise ValueError("未找到有效的分享链接")

    share_url = urls[0]
    share_response = requests.get(share_url, headers=HEADERS)
    video_id = share_response.url.split("?")[0].strip("/").split("/")[-1]
    share_url = f'https://www.iesdouyin.com/share/video/{video_id}'

    # 获取视频页面内容
    response = requests.get(share_url, headers=HEADERS)
    response.raise_for_status()

    pattern = re.compile(
        pattern=r"window\._ROUTER_DATA\s*=\s*(.*?)</script>",
        flags=re.DOTALL,
    )
    find_res = pattern.search(response.text)

    if not find_res or not find_res.group(1):
        print(f"HTML content preview: {response.text[:500]}")
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        raise ValueError("从HTML中解析视频信息失败")

    # 解析JSON数据
    json_data = json.loads(find_res.group(1).strip())
    VIDEO_ID_PAGE_KEY = "video_(id)/page"
    NOTE_ID_PAGE_KEY = "note_(id)/page"

    if VIDEO_ID_PAGE_KEY in json_data["loaderData"]:
        original_video_info = json_data["loaderData"][VIDEO_ID_PAGE_KEY]["videoInfoRes"]
    elif NOTE_ID_PAGE_KEY in json_data["loaderData"]:
        original_video_info = json_data["loaderData"][NOTE_ID_PAGE_KEY]["videoInfoRes"]
    else:
        raise Exception("无法从JSON中解析视频或图集信息")

    data = original_video_info["item_list"][0]

    # 获取视频信息
    video_url = data["video"]["play_addr"]["url_list"][0].replace("playwm", "play")
    desc = data.get("desc", "").strip() or f"douyin_{video_id}"

    # 替换文件名中的非法字符
    desc = re.sub(r'[\\/:*?"<>|]', '_', desc)

    return {
        "url": video_url,
        "title": desc,
        "video_id": video_id
    }

def download_video_direct(video_info: dict) -> str:
    """直接下载视频到指定目录"""
    filename = f"{video_info['title']}.mp4"
    filepath = os.path.join(DOWNLOADS_DIR, filename)

    print(f"正在下载视频: {video_info['title']}")

    response = requests.get(video_info['url'], headers=HEADERS, stream=True)
    response.raise_for_status()

    # 获取文件大小
    total_size = int(response.headers.get('content-length', 0))

    # 下载文件，显示进度
    with open(filepath, 'wb') as f:
        downloaded = 0
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    progress = (downloaded / total_size) * 100
                    print(f"下载进度: {progress:.1f}%", end='\r')

    print(f"\n视频下载完成: {filepath}")
    return filepath

@app.get("/", summary="API 健康检查")
def read_root():
    """检查 API 是否正常运行。"""
    return {"status": "ok", "message": "Douyin Downloader API is running."}

@app.post("/download", summary="下载抖音视频")
def download_video(request: VideoRequest):
    """
    接收一个包含 'url' 的 JSON 请求，然后下载抖音视频（无水印）。
    """
    douyin_url = request.url
    if "douyin.com" not in douyin_url and "iesdouyin.com" not in douyin_url:
        raise HTTPException(status_code=400, detail="无效的抖音链接，请检查 URL。")

    try:
        # 解析抖音分享链接获取视频信息
        print(f"正在解析抖音链接: {douyin_url}")
        video_info = parse_douyin_share_url(douyin_url)

        # 直接下载视频
        file_path = download_video_direct(video_info)

        return {
            "status": "success",
            "message": "视频下载成功（无水印版本）。",
            "file_path": file_path,
            "video_info": {
                "title": video_info["title"],
                "video_id": video_info["video_id"],
                "download_url": video_info["url"]
            }
        }

    except Exception as e:
        error_message = str(e)
        print(f"下载失败: {error_message}")
        raise HTTPException(status_code=500, detail=f"下载过程中发生错误: {error_message}")
