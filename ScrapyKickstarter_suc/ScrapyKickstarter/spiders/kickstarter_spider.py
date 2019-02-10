import scrapy,json,time
import urllib
from scrapy.selector import Selector
from scrapy.exceptions import CloseSpider
from ScrapyKickstarter.items import ProjectInfo
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#Successful projects
URL = "https://www.kickstarter.com/discover/advanced?state=successful&category_id=12&woe_id=23424977&sort=popularity&seed=2572311&page=%d"

# < 75%
#URL = "https://www.kickstarter.com/discover/advanced?category_id=12&woe_id=23424977&raised=0&sort=popularity&seed=2572311&page=%d"

# [75%, 100%]
#URL = "https://www.kickstarter.com/discover/advanced?category_id=12&woe_id=23424977&raised=1&sort=popularity&seed=2572311&page=%d"

videoloc = "/Users/SammiFu/Desktop/task1/newResults/video/"

class KickstarterSpider(scrapy.Spider):
    name = "kickstarter"
    allowed_domains = ["kickstarter.com"]
    start_urls = [URL % 1]

    def __init__(self):
        self.popularity = 0
        self.page_number = 0

    def formatStr(self, input):
        return str(input.encode('utf-8')).strip()

    def formatNum(self, input):
        return str(input).strip()

    def formatList(self, input):
        return map(str.strip, [x.encode('ascii', 'ignore').decode('ISO-8859-1').encode('utf-8') for x in input])

    def percentage(part, whole):
        return 100 * float(part) / float(whole)

    def parse(self, response):
        self.page_number += 1
        print self.page_number
        print "----------"
        sel = Selector(response)
        project = sel.xpath(
            '//section[@id="projects"]/div[@class="grid-container"]/div[@class="js-project-group"]/div[contains(@class, "grid-row")]/div[contains(@class, "js-react-proj-card")]/@data-project').extract()
        if not project:
            raise CloseSpider('No more pages')

        self.popularity = 0
        for p in project:
            pStr = "{" + str(p.encode('utf-8'))[1: -1] + "}"
            projectJson = json.loads(pStr)

            #check if the project is not live project
            if projectJson['state'] != "successful":
                continue

            projectInfo = ProjectInfo()
            projectInfo["ProjectResults"] = {
                "FundedOrNot": self.formatStr(projectJson['state']),
                "AmountAsked": self.formatNum(projectJson['goal']),
                "AmountPledged": self.formatNum(projectJson['pledged']),
                "current_currency": self.formatStr(projectJson['current_currency']),
                "totalBackers": self.formatNum(projectJson['backers_count']),
                "goalFinishedPercentage": self.formatNum(projectJson['percent_funded'])
            }

            projectInfo["ProjectTitle"] = self.formatStr(projectJson['name'])
            projectInfo["ProjectDescription"] = self.formatStr(projectJson['blurb'])
            projectInfo["CreatedBy"] = self.formatStr(projectJson['creator']['name'])

            project_url = str(projectJson['urls']['web']['project'].encode('utf-8'))

            projectInfo["ProjectLink"] = project_url

            self.popularity += 1

            request = scrapy.Request(project_url, callback=self.parse_project_detail)
            request.meta["projectInfo"] = projectInfo
            yield request

            curPage = response.request.url[response.request.url.index("page=")+5:]
            projectInfo["popularity"] = 12*(int(curPage) - 1) + self.popularity

        yield scrapy.Request(URL % self.page_number)



    # supports, champaign,
    def parse_project_detail(self, response):
        projectInfo = response.meta['projectInfo']
        sel = Selector(response)

        # Project Supports
        allLevels = []
        levelbase = '//div[@class="NS_projects__rewards_list js-project-rewards"]/ol/li[@class="hover-group pledge--inactive pledge-selectable-sidebar"]'
        levelname = sel.xpath(levelbase + '/div[@class="pledge__info"]/h2/span[@class="money"]/text()').extract()
        levelTitle = sel.xpath(levelbase + '/div[@class="pledge__info"]/h3/text()').extract()
        pledgeRewardDescription = sel.xpath(levelbase + '/div[@class="pledge__info"]'
                                                      '/div[@class="pledge__reward-description pledge__reward-description--expanded"]'
                                                      '/p/text()').extract()
        pledgeEstimateDelivery = sel.xpath(levelbase +
                                           '/div[@class="pledge__info"]/div[@class="pledge__extra-info"]'
                                           '/div[@class="pledge__detail"]/span[@class="pledge__detail-info"]/time/text()').extract()

        pledgeTotalBackers = sel.xpath(levelbase + '/div[@class="pledge__info"]/div[@class="pledge__backer-stats"]/'
                                                 'span/text()').extract()
        totalCount = int(len(sel.xpath(levelbase)))


        if totalCount > 0:
            for i in range(0, totalCount):
                pl = "null" if i >= len(levelname) else self.formatStr(levelname[i])
                pt = "null" if i >= len(levelTitle) else self.formatStr(levelTitle[i])
                prd = "null" if i >= len(pledgeRewardDescription) else self.formatStr(
                    pledgeRewardDescription[i])
                ped = "null" if i >= len(pledgeEstimateDelivery) else self.formatStr(
                    pledgeEstimateDelivery[i])
                ptb = "null" if i >= len(pledgeTotalBackers) else self.formatStr(
                    pledgeTotalBackers[i])

                reward = {
                    "pledgeLevel": pl,
                    "pledgeTitle": pt,
                    "pledgeRewardDescription": prd,
                    "pledgeEstimateDelivery": ped,
                    "pledgeTotalBackers": ptb
                }

                allLevels.append(reward)

        supports = {
            "totalLevels": totalCount,
            "RewardsOfEachLevels": allLevels
        }

        # Project Champaign
        ti = len(sel.xpath('*//div[@class="template asset"]/figure/img'))

        # Format champaign text
        tmp = self.formatList(sel.xpath(
            '*//div[@class="full-description js-full-description responsive-media formatted-lists"]//text()').extract())
        des = [x for x in tmp if len(x) != 0]

        # Check Video
        # video = sel.css("video").xpath('//source/@src').extract()

        # Project timeline
        projectInfo['ProjectTimeLine'] = self.formatList(sel.xpath('//div[@class="NS_campaigns__funding_period"]/p/time/@datetime').extract())
        projectInfo['ProjectSupports'] = json.dumps(supports)
        projectInfo['ImageCaption'] = des
        projectInfo['TotalImage'] = ti
        projectInfo['totalComments'] = sel.xpath('//span[@class="count"]/data/@data-value').extract()[0]

        #ChampaignVideo
        #ChampaignVideoLink
        if len(video) >= 2:
            projectInfo['ChampaignVideo'] = "True"
            projectInfo['ChampaignVideoLink'] = video[1]
            url = video[1]
            name = projectInfo["ProjectTitle"]
            # name = videoloc + name + ".mp4"
            #
            # try:
            #     print("Downloading starts...\n")
            #     urllib.urlretrieve(url, name)
            #     print("Download completed..!!")
            # except Exception as e:
            #     print(e)
        else:
            projectInfo['ChampaignVideo'] = "False"
            projectInfo['ChampaignVideoLink'] = "No Link"

        project_url_update = response.request.url + '/updates'

        request = scrapy.Request(project_url_update, callback=self.parse_project_update)
        request.meta["projectInfo"] = projectInfo

        return request


    #timelime, updates between each timelime
    def parse_project_update(self, response):
        projectInfo = response.meta['projectInfo']
        sel = Selector(response)
        idx, shipCount, sucCount, lauCount = 0, 0, 0, 0
        for c in sel.xpath('*//div[@class="timeline"]/div/@class').extract():
            cc = self.formatStr(c)
            if "launched" in cc:
                tmp = idx - sucCount
                lauCount = 0 if tmp <= 0 else tmp
            elif "successful" in cc:
                tmp = idx - shipCount
                sucCount = 0 if tmp <= 0 else tmp
            elif "ship" in cc:
                shipCount = idx
            elif "item" in cc:
                idx += 1

        projectInfo['ProjectUpdates'] = {
            "totalUpdatesBeforeFunded": lauCount,
            "totalUpdatesBetweenFundedAndShipped": sucCount,
            "totalUpdatesAfterShipped": shipCount
        }

        project_url_comments = response.request.url[:response.request.url.index("/updates")] + '/comments'
        request = scrapy.Request(project_url_comments, callback=self.parse_project_comments)
        request.meta["projectInfo"] = projectInfo

        return request



    def parse_project_comments(self, response):
        projectInfo = response.meta['projectInfo']
        driver = webdriver.Firefox()
        driver.get(response.request.url)
        wait = WebDriverWait(driver, 5)
        click_more = True
        count = 0

        items = []

        try:
            # load comments section
            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//ul[@class="bg-grey-100 border border-grey-400 p2 mb3"]'))
            )
            # automate click operations to load all comments
            while click_more and len(items) < 1000:
                time.sleep(0.5)
                loadmore = driver.find_element_by_id('react-project-comments').find_elements(By.XPATH,
                                                                                                 "//button[contains(@class,'bttn')]")
                items = driver.find_elements(By.XPATH,
                                                 '*//ul[@class="bg-grey-100 border border-grey-400 p2 mb3"]//div[@class="flex mb3"]')
                if loadmore:
                    loadmore[0].click()
                else:
                    click_more = False
                    time.sleep(1)

            # differentiate comments and count the results
            for item in items:
                time.sleep(0.3)
                text = self.formatStr(item.text)
                if "Creator" in text or "Collaborator" in text:
                    count += 1

        except Exception:
            projectInfo['totalVCommentsSample'] = "no comments"
            projectInfo['totalVCommentsPercent'] = "no percent"
            return projectInfo

        else:
            projectInfo['totalVCommentsSample'] = len(items) - count
            if len(items) == 0:
                projectInfo['totalVCommentsPercent'] = 0
            else:
                projectInfo['totalVCommentsPercent'] = 100 * float(projectInfo['totalVCommentsSample']) / float(len(items))
            return projectInfo

        finally:
            driver.quit()










