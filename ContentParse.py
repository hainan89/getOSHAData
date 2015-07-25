from BrowserShadow import BrowserShadow
from bs4 import BeautifulSoup
import mysql.connector
import sys, os


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
        EventDate = item_list[3].get_text()
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

        #print(SummaryNr)
        brw_d = BrowserShadow()
        res_d = brw_d.open_url(accident_url_str)
        page_content_d = res_d.read()
        page_soup_d = BeautifulSoup(page_content_d, "html.parser")

        # parse the detail information about the event
        abstract_info = {'SummaryNr':SummaryNr , 'EventDate':EventDate, 'ReportID':ReportID, 'Fat':str(Fat), 'SIC':SIC, 'EventDesc':EventDesc}
        parse_accident_details(page_soup_d , abstract_info)

        break


        
def parse_accident_details(page_soup_d, abstract_info):

    #obtian the cursor of the mysql connection
    user = 'test'
    pwd = '123456'
    host = '127.0.0.1'
    db = 'reported_fall_event'
    cnx = mysql.connector.connect(user=user, password=pwd, host=host, database=db)
    cursor = cnx.cursor()

    event_content_details = page_soup_d.find_all('tr')

    # base on the position of the keyworks
    # to get the location of the employee and inspection information in this page
    for index in range(0, len(event_content_details)):
        if event_content_details[index].get_text().find('Keywords') > -1 :
            keyword_position = index


    EventDescD = event_content_details[keyword_position - 1].get_text()
    Keyworkds = event_content_details[keyword_position].get_text().replace('Keywords:', '')
    EndUse = event_content_details[keyword_position + 2].find_all('td')[0].get_text()
    ProjType = event_content_details[keyword_position + 2].find_all('td')[1].get_text()
    ProjCost = event_content_details[keyword_position + 2].find_all('td')[2].get_text()
    Stories = event_content_details[keyword_position + 2].find_all('td')[3].get_text()
    NonBldgHt = event_content_details[keyword_position + 2].find_all('td')[4].get_text()

    # insert the case information
    """
    cases_info_str = 'SummaryNr, EventDate, ReportID, Fat, SIC, EventDesc, '
    cases_info_str = cases_info_str + 'EventDescD, Keywords, EndUse, '
    cases_info_str = cases_info_str + 'ProjType, ProjCost, Stories, NonbldgHt'

    cases_info_value_str = "'" + str(abstract_info['SummaryNr']) + "'" + ','
    cases_info_value_str = cases_info_value_str + "'" + str(abstract_info['EventDate']) + "'"   + ','
    cases_info_value_str = cases_info_value_str + "'" + str(abstract_info['ReportID']) + "'"   + ','
    cases_info_value_str = cases_info_value_str + str(abstract_info['Fat']) + ','
    cases_info_value_str = cases_info_value_str + "'" + str(abstract_info['SIC']) + "'"   + ','
    cases_info_value_str = cases_info_value_str + "'" + str(abstract_info['EventDesc']) + "'"   + ','
    cases_info_value_str = cases_info_value_str + "'" + str(EventDescD) + "'"  + ','
    cases_info_value_str = cases_info_value_str + "'" + str(Keyworkds) + "'"   + ','
    cases_info_value_str = cases_info_value_str + "'" + str(EndUse) + "'"   + ','
    cases_info_value_str = cases_info_value_str + "'" + str(ProjType) + "'"   + ','
    cases_info_value_str = cases_info_value_str + "'" + str(ProjCost) + "'" + ','
    cases_info_value_str = cases_info_value_str + str(Stories) + ','
    cases_info_value_str = cases_info_value_str + str(NonBldgHt)
    
    insert_case_info_sql_str = "insert into cases_info({case_info}) values ({case_info_value})"
    insert_case_info_sql_str = insert_case_info_sql_str.format(case_info = cases_info_str, case_info_value = cases_info_value_str)
    """

    insert_sql_str = ("insert into cases_info "
                      "(SummaryNr, EventDate, ReportID, Fat, SIC, EventDesc, "
                      "EventDescD, Keywords, EndUse, ProjType, ProjCost, Stories, NonbldgHt)"
                      "values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")

    insert_values = (abstract_info['SummaryNr'], abstract_info['EventDate'], abstract_info['ReportID'],abstract_info['Fat'],abstract_info['SIC'],abstract_info['EventDesc'],
                     EventDescD, Keyworkds, EndUse, ProjType, ProjCost, Stories, NonBldgHt)
    
    #print(insert_case_info_sql_str)
    """
    try:
        cursor.execute(insert_sql_str, insert_values)
        print('=============================')
        print('insert cases_info')
        print('=============================')
        cnx.commit()
    except mysql.connector.Error as err:
        print("Insert cases_info Table Failed.")
        print("Error: {}".format(err.msg))
        sys.exit()
    """
    
    for index in range(2, keyword_position - 1, 2):
        current_insp_id = event_content_details[index].find_all('td')[0].get_text()
        current_insp_date = event_content_details[index].find_all('td')[1].get_text()
        current_insp_sic = event_content_details[index].find_all('td')[2].get_text()
        current_insp_establishment_name = event_content_details[index].find_all('td')[3].get_text()
        #print(current_insp_id + '--' + current_insp_date + '--' + current_insp_sic + '--' + current_insp_establishment_name)

        # insert into table inspection_info
        """
        insp_info_str = 'InspectionID, OpenDate, SIC, EstablishmentName'

        insp_info_value_str = "'" + str(current_insp_id) + "'" + ','
        insp_info_value_str = insp_info_value_str + "'" + str(current_insp_date) + "'" + ','
        insp_info_value_str = insp_info_value_str + "'" + str(current_insp_sic) + "'" + ','
        insp_info_value_str = insp_info_value_str + "'" + str(current_insp_establishment_name) + "'"

        insert_insp_info_sql_str = "insert into inspection_info({insp_info}) values ({insp_info_value})"
        insert_insp_info_sql_str = insert_insp_info_sql_str.format(insp_info = insp_info_str, insp_info_value = insp_info_value_str)

        print(insert_insp_info_sql_str)
        """

        insert_sql_str = ("insert into inspection_info "
                      "(InspectionID, OpenDate, SIC, EstablishmentName)"
                      "values(%s, %s, %s, %s)")

        insert_values = (current_insp_id, current_insp_date, current_insp_sic,current_insp_establishment_name )

        """
        try:
            cursor.execute(insert_sql_str, insert_values)
            print('=============================')
            print('insert inspection_info')
            print('=============================')
            cnx.commit()
        except mysql.connector.Error as err:
            print("Insert inspection_info Table Failed.")
            print("Error: {}".format(err.msg))
            sys.exit()
        break
        """

    for index in range(keyword_position + 4, len(event_content_details)):
        current_employee_eid = event_content_details[index].find_all('td')[0].get_text()
        current_employee_insp_id = event_content_details[index].find_all('td')[1].get_text()
        current_employee_age = event_content_details[index].find_all('td')[2].get_text()
        current_employee_sex = event_content_details[index].find_all('td')[3].get_text()
        current_employee_degree = event_content_details[index].find_all('td')[4].get_text()
        current_employee_nature = event_content_details[index].find_all('td')[5].get_text()
        current_employee_occupation = event_content_details[index].find_all('td')[6].get_text()

        construction_str = str(event_content_details[index].find_all('td')[7])
        construction_str = construction_str.replace('<td>' , '')
        construction_str = construction_str.replace('</td>' , '')
        construction_str = construction_str.replace('<b>' , '')
        construction_str = construction_str.replace('</b>' , '')
        construction_str = construction_str.replace('</br>' , '')
        construction_list = construction_str.split('<br>')
        current_employee_consruction = "{"
        for index in range(0, len(construction_list) - 1):
            item_one_name = construction_list[index].split(':')
            current_employee_consruction = current_employee_consruction + "'"+item_one_name[0]+"':'"+item_one_name[1] + "',"
        item_one_name = construction_list[index + 1].split(':')
        current_employee_consruction =current_employee_consruction + "'"+item_one_name[0]+"':'"+item_one_name[1] + "'}"
        #print(current_employee_eid + '--' + current_employee_insp_id + '--' + current_employee_age + '--' + current_employee_sex + '--' + current_employee_degree + '--' + current_employee_nature + '--' + current_employee_occupation + '--' + current_employee_consruction)

        """
        employee_info_str = 'EID, SummaryNr, InspectionID, Age, Sex, Degree, Nature, Occupation, Construction'
        employee_info_value_str = str(current_employee_eid) + ','
        employee_info_value_str = employee_info_value_str + "'" + str(abstract_info['SummaryNr']) + "'" + ','
        employee_info_value_str = employee_info_value_str + "'" + str(current_employee_insp_id) + "'" + ','
        employee_info_value_str = employee_info_value_str + "'" + str(current_employee_age) + "'" + ','
        employee_info_value_str = employee_info_value_str + "'" + str(current_employee_sex) + "'" + ','
        employee_info_value_str = employee_info_value_str + "'" + str(current_employee_degree) + "'" + ','
        employee_info_value_str = employee_info_value_str + "'" + str(current_employee_nature) + "'" + ','
        employee_info_value_str = employee_info_value_str + "'" + str(current_employee_occupation) + "'" + ','
        employee_info_value_str = employee_info_value_str + '"' + str(current_employee_consruction) + '"'

        insert_employee_info_sql_str = "insert into case_employees({emp_info}) values ({emp_info_value})"
        insert_employee_info_sql_str = insert_employee_info_sql_str.format(emp_info = employee_info_str, emp_info_value = employee_info_value_str)

        print(insert_employee_info_sql_str)
        """

        insert_sql_str = ("insert into case_employees "
                      "(EID, SummaryNr, InspectionID, Age, Sex, Degree, Nature, Occupation, Construction)"
                      "values(%s, %s, %s, %s, %s, %s, %s, %s, %s)")

        insert_values = (current_employee_eid, abstract_info['SummaryNr'], current_employee_insp_id,current_employee_age,
                         current_employee_sex, current_employee_degree, current_employee_nature, current_employee_occupation, current_employee_consruction)
        
        try:
            cursor.execute(insert_sql_str, insert_values)
            print('=============================')
            print('insert case_employees')
            print('=============================')
            cnx.commit()
        except mysql.connector.Error as err:
            print("Insert case_employees Table Failed.")
            print("Error: {}".format(err.msg))
            sys.exit()
        break
            
    cursor.close()
    cnx.close()
    
    

get_record_list(15, '15', '06', '1989', '15', '06', '2015')
#article_info_list = get_articles_list(15, 0 , 0)
#get_article_content(article_info_list)
