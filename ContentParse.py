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
    #print(search_url)

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
        #print(search_url)
        brw = BrowserShadow()
        res = brw.open_url(search_url)
        page_content = res.read()
        page_soup = BeautifulSoup(page_content, "html.parser")

        # prase the specified record
        """collect the records into mysql database"""
        parse_page_obtian_event(page_soup)
        break


        checked_num = checked_num + p_show
        #print(checked_num)
        if checked_num == record_num:
            break
        else:
            p_finish = p_finish + p_show
       
""" end get_articles_list""" 


def parse_page_obtian_event(page_soup):
    #event_content = page_soup.select('#maintain')[0].select('.row-fluid')[0].select('.table-responsive')[0].select('tbody')[0]
    event_content = page_soup.select('#maincontain')[0].select('.row-fluid')[0].select('.table-responsive')[1].select('table')[0].find_all('tr')

    for index in range(1 , len(event_content)):
        item_list = event_content[index].find_all('td')
        SummaryNr = item_list[2].find('a').get_text()
        EventData = item_list[3].get_text()
        ReportID = item_list[4].get_text()
        Fat = item_list[5].get_text()
        if Fat.find('X') > -1 :
            Fat = 1
        else:
            Fat = 0

        SIC = item_list[6].find('a').get_text()
        EventDesc = item_list[7].get_text()
        #print(SummaryNr + EventData + ReportID + str(Fat) + SIC)

        accident_url_str = item_list[2].find('a')['href']
        accident_url_str = 'https://www.osha.gov/pls/imis/' + accident_url_str

        print(SummaryNr)
        brw_d = BrowserShadow()
        res_d = brw_d.open_url(accident_url_str)
        page_content_d = res_d.read()
        page_soup_d = BeautifulSoup(page_content_d, "html.parser")
        parse_accident_details(page_soup_d)


        
def parse_accident_details(page_soup_d):

    event_content_details = page_soup_d.find_all('tr')

    # base on the position of the keyworks
    # to get the location of the employee and inspection information in this page
    for index in range(0, len(event_content_details)):
        if event_content_details[index].get_text().find('Keywords') > -1 :
            keyword_position = index


    EventDescD = event_content_details[keyword_position - 1]
    Keyworkds = event_content_details[keyword_position]
    EndUse = event_content_details[keyword_position + 2].find_all('td')[0]
    ProjType = event_content_details[keyword_position + 2].find_all('td')[1]
    ProjCost = event_content_details[keyword_position + 2].find_all('td')[2]
    Stories = event_content_details[keyword_position + 2].find_all('td')[3]
    NonBldgHt = event_content_details[keyword_position + 2].find_all('td')[4]

    inspection_num = 0
    for index in range(2, keyword_position - 1, 2):
        current_insp_id = event_content_details[index].find_all('td')[0].get_text()
        current_insp_date = event_content_details[index].find_all('td')[1].get_text()
        current_insp_sic = event_content_details[index].find_all('td')[2].get_text()
        current_insp_establishment_name = event_content_details[index].find_all('td')[3].get_text()
        #print(current_insp_id + '--' + current_insp_date + '--' + current_insp_sic + '--' + current_insp_establishment_name)
        inspection_num = inspection_num + 1

    employee_num = 0
    for index in range(keyword_position + 4, len(event_content_details)):
        current_employee_eid = event_content_details[index].find_all('td')[0].get_text()
        current_employee_insp_id = event_content_details[index].find_all('td')[1].get_text()
        current_employee_age = event_content_details[index].find_all('td')[2].get_text()
        current_employee_sex = event_content_details[index].find_all('td')[3].get_text()
        current_employee_degree = event_content_details[index].find_all('td')[4].get_text()
        current_employee_nature = event_content_details[index].find_all('td')[5].get_text()
        current_employee_occupation = event_content_details[index].find_all('td')[6].get_text()
        current_employee_consruction = event_content_details[index].find_all('td')[7].get_text()

        #print(current_employee_eid + '--' + current_employee_insp_id + '--' + current_employee_age + '--' + current_employee_sex + '--' + current_employee_degree + '--' + current_employee_nature + '--' + current_employee_occupation + '--' + current_employee_consruction)
        employee_num = employee_num + 1

    #print(inspection_num)
    #print(employee_num)
    
        
get_record_list(15, '15', '06', '1989', '15', '06', '2015')
#article_info_list = get_articles_list(15, 0 , 0)
#get_article_content(article_info_list)
