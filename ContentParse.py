from BrowserShadow import BrowserShadow
from bs4 import BeautifulSoup


# query the total number of the records
def get_record_num(SICNo, s_d, s_m, s_y, e_d, e_m, e_y):
    sic_str = 'sic={sic}&'
    s_d_str = 'startday={s_d}&'
    s_m_str = 'startmonth={s_m}&'
    s_y_str = 'startyear={s_y}&'
    e_d_str = 'endday={e_d}&'
    e_m_str = 'endmonth={e_m}&'
    e_y_str = 'endyear={e_y}&'

    search_url = 'https://www.osha.gov/pls/imis/AccidentSearch.search?'
    search_url = search_url + 'p_logger=1&acc_description=fall&acc_Abstract=&acc_keyword=&'
    search_url = search_url + sic_str.format(sic=SICNo)
    search_url = search_url + 'naics=&Office=All&officetype=All&'
    search_url = search_url + e_m_str.format(e_m=e_m)
    search_url = search_url + e_d_str.format(e_d=e_d)
    search_url = search_url + e_y_str.format(e_y=e_y)
    search_url = search_url + s_m_str.format(s_m=s_m)
    search_url = search_url + s_d_str.format(s_d=s_d)
    search_url = search_url + s_y_str.format(s_y=s_y)
    search_url = search_url + 'InspNr='

    brw = BrowserShadow()
    res = brw.open_url(search_url)
    page_content = res.read()
    page_soup = BeautifulSoup(page_content, "html.parser")

    count_str_cell = page_soup.select('#maincontain')[0].select('.row-fluid')[0].select('.row-fluid')[0].select('.span3')[0].select('.text-right')
    count_str = count_str_cell[0].get_text();
    record_num = int(count_str[count_str.find('of') + 2 : len(count_str)])
    
    #print(record_num)
    print(search_url)

    return record_num


def get_record_list(SICNo, s_d, s_m, s_y, e_d, e_m, e_y):

    record_num = get_record_num(SICNo, s_d, s_m, s_y, e_d, e_m, e_y)

    if record_num <= 0:
        print("No Eligible Record has been retrieved!")
        return

    
    p_finish = 0
    p_show = 100
    if record_num < p_show:
        p_show = record_num

    checked_num = 0
    while 1:

        if (p_finish + p_show) > record_num:
            p_show = record_num - p_finish
        
        sic_str = 'sic={sic}&'
        p_finish_str = 'p_finish={p_finish}&'
        p_show_str = 'p_show={p_show}'

        search_url = 'https://www.osha.gov/pls/imis/accidentsearch.search?'
        search_url = search_url + sic_str.format(sic=SICNo)
        search_url = search_url + 'sicgroup=&naics=&acc_description=fall&acc_abstract=&acc_keyword=&inspnr=&fatal=&officetype=All&office=All&'
        search_url = search_url + 'startmonth=07&startday=24&startyear=2015&endmonth=07&endday=23&endyear=1984&keyword_list=&p_start=&'
        search_url = search_url + p_finish_str.format(p_finish=p_finish)
        search_url = search_url + 'p_sort=&p_desc=DESC&p_direction=Next&'
        search_url = search_url + p_show_str.format(p_show=p_show)

        brw = BrowserShadow()
        res = brw.open_url(search_url)
        page_content = res.read()
        page_soup = BeautifulSoup(page_content, "html.parser")


        # prase the specified record
        """collect the records into mysql database"""

        


        checked_num = checked_num + p_show
        print(checked_num)
        if checked_num == record_num:
            break
        else:
            p_finish = p_finish + p_show
       
""" end get_articles_list""" 

get_record_list(15, '15', '06', '1989', '15', '06', '2015')
#article_info_list = get_articles_list(15, 0 , 0)
#get_article_content(article_info_list)
