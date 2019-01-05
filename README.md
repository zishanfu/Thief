# Thief
This repository contains the web crawler projects.

## Instructions
Install the needed python packages scrapy selenium  
Configurate the paths in the file  
Run the scrapy by **scrapy crawl kickstarter**  

## ScrapyKickstarter
The project scrapy the data from kickstarter, format data and save in file.

```
    ProjectTitle = scrapy.Field()
    ProjectDescription = scrapy.Field()
    CreatedBy = scrapy.Field()
    popularity = scrapy.Field()
    ProjectTimeLine = scrapy.Field()
    ProjectUpdates = scrapy.Field()
    totalComments = scrapy.Field()
    totalVCommentsSample = scrapy.Field()
    totalVCommentsPercent = scrapy.Field()
    ProjectResults = scrapy.Field()
    ProjectSupports = scrapy.Field()
    ProjectChampaign = scrapy.Field()
```

The ProxyList is from [proxy-list](https://github.com/clarketm/proxy-list). In order to use the project, please check and update the status of the proxy list.
