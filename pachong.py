import requests
from bs4 import BeautifulSoup
import time
import random
import csv
from urllib.parse import urljoin

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive'
}

class Website:
    # 存放TOP250页面的信息
    def __init__(self, name, url):
        self.name = name  # 为豆瓣top250
        self.url = url    # 这个top250的页面

class Detail:
    # 存储单个电影的名字、评论和标签
    def __init__(self, url):
        self.url = url    # 详情页URL
        self.title = ""   # 标题
        self.comments = []  # 短评
        self.tags = []    # 电影的标签


class Crawler:
    # 爬虫类
    def __init__(self, site, limit=5, custom_cookies=None):
        self.site = site
        self.limit = limit  # 限制爬取的电影数量
        self.movie_details = []  # 存储所有电影对应的Detail对象
        self.session = None  # 会话对象
        self.custom_cookies = custom_cookies  # 自定义Cookie

#获取页面
    def get_page(self, url):
        if not self.session:
            self.session = requests.Session()
            self.session.headers = HEADERS
            # 设置自定义Cookie（如果提供）
            #if self.custom_cookies:
            self.session.cookies.update(self.custom_cookies)
            # 先访问首页以初始化会话
            self.session.get("https://movie.douban.com", timeout=10)
        try:
            time.sleep(random.uniform(1, 3))
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"请求异常: {e}")
            return None

#获取评论
    def get_Comment(self):
        print(f"\n开始爬取 {len(self.movie_details)} 部电影的短评...")
        for detail in self.movie_details:
            title = self.get_movie_title(detail.url)  # 获取电影标题
            tags = self.get_movie_tag(detail.url)     # 获取电影标签
            detail.title = title
            detail.tags = " ".join(tags) if tags else ""  # 标签用空格拼接
            print(f"\n正在爬取电影: {title} 的短评，标签: {detail.tags}")

            # 构建短评页面URL
            comment_url = urljoin(detail.url, "comments?status=P")
            page_num = 1
            page_size = 20
            max_pages = 20  # 最多爬取20页

            while page_num <= max_pages:
                print(f"  正在爬取第 {page_num} 页短评: {comment_url}")
                bs = self.get_page(comment_url)
                if not bs:
                    print(f"  第 {page_num} 页获取失败")
                    break

                # 提取评论内容
                comment_elements = bs.select(".comment-item .short")
                for element in comment_elements:
                    comment_text = element.get_text(strip=True)
                    detail.comments.append(comment_text)

                # 查找下一页链接
                next_page = bs.select_one("a.next")
                if next_page and 'href' in next_page.attrs:
                    movie_id = detail.url.split('/')[-2]
                    page_start = page_size * page_num
                    comment_url = f"https://movie.douban.com/subject/{movie_id}/comments?start={page_start}&limit={page_size}&sort=new_score&status=P"
                    page_num += 1
                else:
                    print(f"共爬取 {page_num - 1} 页")
                    break

            print(f"电影 {title} 共爬取到 {len(detail.comments)} 条评论")
            time.sleep(random.uniform(2, 4))

        # 计算并打印总评论数
        total_comments = sum(len(detail.comments) for detail in self.movie_details)
        print(f"\n共爬取到 {total_comments} 条短评")
        # 保存评论到CSV
        self.save_comments_to_csv()

    def get_movie_title(self, url):
        #获取标题
        bs = self.get_page(url)
        if bs:
            title = bs.select_one('[property="v:itemreviewed"]')
            if title:
                return title.get_text(strip=True)
        return ""

#获取电影标签
    def get_movie_tag(self, url):
        tags = []
        bs = self.get_page(url)
        if bs:
            tag_elements = bs.select("[property='v:genre']")
            if tag_elements:
                for tag in tag_elements:
                    tag_text = tag.get_text(strip=True)
                    #if tag_text:
                    tags.append(tag_text)
        return tags

#保存数据到csv
    def save_comments_to_csv(self):
        all_comments = []
        for detail in self.movie_details:
            for comment in detail.comments:
                all_comments.append({
                    'movie_title': detail.title,
                    'comment': comment,
                    'tag': detail.tags
                })

        if not all_comments:
            print("没有短评可保存")
            return

        filename = "comments.csv"
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=['movie_title', 'comment', 'tag'])
                writer.writeheader()
                writer.writerows(all_comments)
            print(f"已将 {len(all_comments)} 条短评保存到 {filename}")
        except Exception as e:
            print(f"保存出错: {e}")

    def crawl(self):
        print(f"开始爬取: {self.site.name} ({self.site.url})")
        bs = self.get_page(self.site.url)
        if bs:
            movie_links = bs.select("div.item > div.info > div.hd > a")
            movie_links = movie_links[:self.limit]
            print(f"将爬取前 {len(movie_links)} 部电影的详情")

            for link in movie_links:
                movie_name = link.select_one('span.title').get_text(strip=True)
                detail_url = link.get('href')
                if detail_url:
                    print(f"找到电影: {movie_name}, 链接: {detail_url}")
                    detail = Detail(detail_url)
                    self.movie_details.append(detail)
                else:
                    print(f"无法获取电影 {movie_name} 的详情页")
                time.sleep(random.uniform(1, 2))

        print(f"\n共爬取到 {len(self.movie_details)} 个电影链接")
        if self.movie_details:
            self.get_Comment()
        return self.movie_details


if __name__ == "__main__":
    # 自行填入Cookie
    custom_cookies = {}

    douban_site = Website('豆瓣电影Top250', 'https://movie.douban.com/top250')
    crawler = Crawler(douban_site, limit=1, custom_cookies=custom_cookies)
    movie_details = crawler.crawl()