import os
import re
import yaml
import datetime
import requests
import warnings
import pandas as pd
from read_pdf import read_pdf_from_url

warnings.simplefilter(action='ignore')

VACC_STA = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_outputs', 'vaccination_state_level.txt')
VACC_DST = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_outputs', 'vaccination_district_level.csv')
VACC_DST_COWIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_outputs', 'vaccination_cowin_district_level.csv')
VACC_OUTPUT_MOHFW = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_outputs', 'vaccination_mohfw.csv')

STATES_YAML = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'states.yaml')
DISTRICTS_DATA_SHEET = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTrt_V4yW0jd91chhz9BJZOgJtFrsaZEa_gPlrFfQToBuuNDDkn01w0K0GdnjCdklyzFz84A1hFbSUN/pub?gid=382746758&single=true&output=csv'
TODAY = datetime.date.today()

with open(STATES_YAML, 'r') as stream:
    try:
        states_all = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)


def get_vaccation_mohfw():
    '''
    Downloads from PDF files & writes into a PDF file
    NOTE:
    '''
    temp_today = TODAY - datetime.timedelta(days=1)

    base_url = "https://www.mohfw.gov.in/pdf/CummulativeCovidVaccinationReport{}.pdf"
    today_mohfw_str = temp_today.strftime("%d%B%Y")
    today_sheet_str = temp_today.strftime("%d/%m/%Y")
    url = base_url.format(today_mohfw_str.lower())

    # if you change this variable, you'll have to change the function name inside `read_pdf.py` file too
    vacc_mohfw_code = 'vaccination_mohfw'

    opt = {
        'state_code': vacc_mohfw_code,
        'url': url,
        'type': 'pdf',
        'config': {
            'page': 1,
            'start_key': 'A & N Islands',
            'end_key': ''
        }
    }

    # read pdf file and extract text
    read_pdf_from_url(opt)

    df_mohfw = pd.read_csv(VACC_OUTPUT_MOHFW)
    print(df_mohfw)

    # with open(VACC_OUTPUT_MOHFW, "r") as vacc_mohfw:
    #     for line in vacc_mohfw:

    #         # Check if some pdf files end Misc total split to additional lines
    #         if len(line.split(',')) != 1:
    #             if "Miscellaneous" in line:
    #                 # trap & rework Misc
    #                 miscline = line
    #                 continue

    #       IndiaFirstDose += int(line.split(',')[1])
    #       IndiaSecondDose += int(line.split(',')[2])
    #       IndiaTotalDose += int(line.split(',')[3])

      #     if "Dadra" in line or "Daman" in line:
      #       dadra['firstDose'] += int(line.split(',')[1])
      #       dadra['secondDose'] += int(line.split(',')[2])
      #       dadra['totalDose'] += int(line.split(',')[3])
      #       continue

      #     #A & N name mapping
      #     if "A & N Islands" in line:
      #       row += str("{},Andaman and Nicobar Islands,{},{},{}\n".format(todayp, int(line.split(',')[1]), int(line.split(',')[2]), int(line.split(',')[3])))
      #       #print(row)
      #     #J &K name mapping
      #     elif "Jammu & Kashmir" in line:
      #       row += str("{},Jammu and Kashmir,{},{},{}\n".format(todayp, int(line.split(',')[1]), int(line.split(',')[2]), int(line.split(',')[3])))
      #       #print(row)
      #     else:
      #       #print(todayp + "," + line, end = "")
      #       row += str(todayp + "," + line)
      #    else:
      #      #trap & club all misc lines at end
      #      miscline += line
      # #add clubbed Dadra Daman last
      # row += str("{},Dadra and Nagar Haveli and Daman and Diu,{},{},{}\n".format(todayp, dadra['firstDose'], dadra['secondDose'], dadra['totalDose']))

      # #rework on Misc line issue to sortout
      # miscline=miscline.replace ('\n', '')
      # #print(miscline)
      # if miscline != '':
      #   miscFirstDose = int(miscline.split(',')[1])
      #   miscSecondDose = int(miscline.split(',')[2])
      #   miscTotalDose = int(miscline.split(',')[3].lstrip('0'))
      #   IndiaFirstDose += miscFirstDose
      #   IndiaSecondDose += miscSecondDose
      #   IndiaTotalDose += miscTotalDose
      #   row += str("{},Miscellaneous,{},{},{}\n".format(todayp, miscFirstDose, miscSecondDose, miscTotalDose))
      # row += str("{},Total,{},{},{}\n".format(todayp, IndiaFirstDose, IndiaSecondDose, IndiaTotalDose))
     # print(row)



def get_vaccination_state_level(lookback=0):
    '''
    For a given number of days, gets state vaccination data from CoWIN API

    :param: `lookback` <int> - The number of days to pull back from. If 0, then will only take current date

    :returns: None - Appends the output to following files
        vaccination state level -> `_outputs/vaccination_state_level.txt`
    '''
    base_url = 'https://api.cowin.gov.in/api/v1/reports/v2/getPublicReports?state_id={s_id}&district_id={d_id}&date={d}'

    # append code for cases at nation level
    states_all['in'] = {
        'cowin_code': '',
        'name': 'India'
    }

    for day in range (lookback, -1, -1):
        curr_date = TODAY - datetime.timedelta(days=day)
        curr_date_str = curr_date.strftime('%d-%m-%Y')
        # print('Fetching for {}'.format(curr_date_str))
        district_rows = []

        # run for every state
        for state_code in states_all:
            params = {
                's_id': states_all[state_code].get('cowin_code'),
                'd_id': '',
                'd': curr_date.strftime("%Y-%m-%d")
            }
            state_url = base_url.format(**params)
            resp = requests.request('GET', state_url)
            state_data = resp.json()
            age_groups = state_data['vaccinationByAge'] if 'vaccinationByAge' in state_data else state_data['topBlock'].get('vaccination')

            print('printing for ', states_all[state_code].get('name'), '---> all districts', state_url)
            with open(VACC_STA, 'a') as file:
                datum = [
                    curr_date_str, \
                    states_all[state_code].get('name'), \
                    # 'TEST_districtName', \
                    state_data['topBlock'].get('vaccination')['total'], \
                    state_data['topBlock']['sessions']['total'], \
                    state_data['topBlock']['sites']['total'], \
                    state_data['topBlock']['vaccination']['tot_dose_1'], \
                    state_data['topBlock']['vaccination']['tot_dose_2'], \
                    state_data['topBlock']['vaccination']['male'], \
                    state_data['topBlock']['vaccination']['female'], \
                    state_data['topBlock']['vaccination']['others'], \
                    state_data['topBlock']['vaccination']['covaxin'], \
                    state_data['topBlock']['vaccination']['covishield'], \
                    state_data['topBlock']['vaccination'].get('sputnik'), \
                    state_data['topBlock']['vaccination'].get('aefi'), \
                    state_data['vaccinationByAge'].get('vac_18_45'), \
                    state_data['vaccinationByAge'].get('vac_45_60'), \
                    state_data['vaccinationByAge'].get('above_60')
                ]

                datum = ','.join(map(str, datum))
                print(datum, file=file)

def get_vaccination(lookback=0):
    '''
    For a given number of days, gets state and district-wise vaccination data from CoWIN API

    :param: `lookback` <int> - The number of days to pull back from. If 0, then will only take current date

    :returns: None - Writes the output to following files
        vaccination state level -> `_outputs/vaccination_state_level.txt`
        vaccination distr level -> `_outputs/vaccination_district_level.csv`
    '''
    base_url = 'https://api.cowin.gov.in/api/v1/reports/v2/getPublicReports?state_id={s_id}&district_id={d_id}&date={d}'
    states_all['in'] = {
        'cowin_code': '',
        'name': 'India'
    }

    for day in range (lookback, -1, -1):
        curr_date = TODAY - datetime.timedelta(days=day)
        curr_date_str = curr_date.strftime('%d-%m-%Y')
        print('Fetching for {}'.format(curr_date_str))
        district_rows = []

        # run for every state
        for state_code in states_all:
            params = {
                's_id': states_all[state_code].get('cowin_code'),
                'd_id': '',
                'd': curr_date.strftime("%Y-%m-%d")
            }
            state_url = base_url.format(**params)
            print(state_url)
            resp = requests.request('GET', state_url)
            state_data = resp.json()
            age_groups = state_data['vaccinationByAge'] if 'vaccinationByAge' in state_data else state_data['topBlock'].get('vaccination')

            # print('printing for ', states_all[state_code].get('name'), '---> all districts')
            # with open(VACC_STA, 'a') as file:
            #     datum = [
            #         curr_date_str, \
            #         states_all[state_code].get('name'), \
            #         # 'TEST_districtName', \
            #         state_data['topBlock'].get('vaccination')['total'], \
            #         state_data['topBlock']['sessions']['total'], \
            #         state_data['topBlock']['sites']['total'], \
            #         state_data['topBlock']['vaccination']['tot_dose_1'], \
            #         state_data['topBlock']['vaccination']['tot_dose_2'], \
            #         state_data['topBlock']['vaccination']['male'], \
            #         state_data['topBlock']['vaccination']['female'], \
            #         state_data['topBlock']['vaccination']['others'], \
            #         state_data['topBlock']['vaccination']['covaxin'], \
            #         state_data['topBlock']['vaccination']['covishield'], \
            #         state_data['topBlock']['vaccination'].get('sputnik'), \
            #         state_data['topBlock']['vaccination'].get('aefi'), \
            #         state_data['vaccinationByAge'].get('vac_18_45'), \
            #         state_data['vaccinationByAge'].get('vac_45_60'), \
            #         state_data['vaccinationByAge'].get('above_60')
            #     ]

            #     datum = ','.join(map(str, datum))
            #     print(datum, file=file)

            # run for every district within each state
            for district in state_data['getBeneficiariesGroupBy']:
                if states_all[state_code].get('name') != 'India':
                    params = {
                        's_id': states_all[state_code].get('cowin_code'),
                        'd_id': district.get('district_id'),
                        'd': curr_date.strftime("%Y-%m-%d")
                    }
                    district_url = base_url.format(**params)
                    try:
                        resp = requests.request('GET', district_url)
                        district_data = resp.json()
                    except:
                        print(district_url)
                        print(resp)

                    print('printing for ', states_all[state_code].get('name'), '--->', district['title'])
                    with open(VACC_STA, 'a') as file:
                        datum = {
                            'updated_at': curr_date_str, \
                            'State': states_all[state_code].get('name', '').strip(), \
                            'District': district['title'].strip(), \
                            'Total Doses Administered': district_data['topBlock'].get('vaccination').get('total'), \
                            'Sessions': district_data['topBlock'].get('sessions').get('total'), \
                            'Sites': district_data['topBlock'].get('sites').get('total'), \
                            'First Dose Administered': district_data['topBlock'].get('vaccination').get('tot_dose_1'), \
                            'Second Dose Administered': district_data['topBlock'].get('vaccination').get('tot_dose_2'), \
                            'Male(Doses Administered)': district_data['topBlock'].get('vaccination').get('male'), \
                            'Female(Doses Administered)': district_data['topBlock'].get('vaccination').get('female'), \
                            'Transgender(Doses Administered)': district_data['topBlock'].get('vaccination').get('others'), \
                            'Covaxin (Doses Administered)': district_data['topBlock'].get('vaccination').get('covaxin'), \
                            'Covishield (Doses Administered)': district_data['topBlock'].get('vaccination').get('covishield'), \
                            # Enable these if necessary
                            # 'Sputnik (Doses Administered)': district_data['topBlock'].get('vaccination').get('sputnik'), \
                            # 'Aefi': district_data['topBlock'].get('vaccination').get('aefi'), \
                            # '18-45 (Doses administered)': district_data['vaccinationByAge'].get('vac_18_45'), \
                            # '45-60 (Doses administered)': district_data['vaccinationByAge'].get('vac_45_60'), \
                            # 'Above 60 (Doses administered)': district_data['vaccinationByAge'].get('above_60')
                        }

                        district_rows.append(datum)
                        datum = [str(v) for k, v in datum.items()]
                        datum = ','.join(datum)
                        print(datum, file=file)

    print("Making districts data file")
    district_data = pd.DataFrame(district_rows).drop('updated_at', 1)
    district_data.to_csv(VACC_DST_COWIN, index=False)

    print("Getting state-district mapping from google sheet")
    public_data = pd.read_csv(DISTRICTS_DATA_SHEET)
    state_dist_mapping = public_data[['State_Code', 'State', 'Cowin Key', 'District']].drop(0, axis=0)
    merged_data = pd.merge(state_dist_mapping, district_data, left_on=['State', 'Cowin Key'], right_on=['State', 'District'], how='left', suffixes=('', '_cowin'))
    # we are keeping district names from Covid19Bharat's google sheet and ignoring the API ones.
    merged_data = merged_data.drop(['Cowin Key', 'District_cowin'], 1)
    merged_data.columns = pd.MultiIndex.from_tuples([('' if k in ('State_Code', 'State', 'District') else curr_date_str, k) for k in merged_data.columns])

    merged_data.to_csv(VACC_DST, index=False)
    print("District data is saved to: ", VACC_DST)

# calling only state level function (separated)
# get_vaccination_state_level(lookback=1)

# get_vaccination(lookback=0)

get_vaccation_mohfw()
