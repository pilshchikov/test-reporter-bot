import datetime
import time

import broadcaster
import jenkinsapi
import pytz
from pytz import timezone
from settings import params

utc = pytz.utc
eastern = timezone('Asia/Yekaterinburg')

jenkins_url = params.get_config('urls', 'jenkins_url')
tracked_view = params.get_config('urls', 'tracked_view_path')
tracked_view_debug = params.get_config('urls', 'tracked_debug_view_path')

colors = {'SUCCESS': '#36a64f',
          'FAILURE': '#ff0000',
          'UNSTABLE': '#ffff00',
          'DETAIL': '#800080'}

begin_date = datetime.datetime.now(tz=eastern)
last_time = {}


def time_is_after(job_name, build_timestamp):
    if job_name in last_time:
        return build_timestamp > last_time.get(job_name)
    else:
        last_time[job_name] = begin_date
        time_is_after(job_name, build_timestamp)


def jenkins_request(view_type="default"):
    jenkins = jenkinsapi.jenkins.Jenkins(jenkins_url)

    if view_type in 'default':
        view = tracked_view
    else:
        view = tracked_view_debug

    # фетчим джобы из вью
    for job_name in jenkins.get_view_by_url(jenkins_url + view).get_job_dict():
        # последний удачный билд
        try:
            build = jenkins.get_job(job_name).get_last_completed_build()
        except:
            continue
        # если начало билда больше чем начало предыдущего замера, то берем в работу
        if build is not None and time_is_after(job_name, build.get_timestamp().astimezone(eastern)):
            timestamp = build.get_timestamp().astimezone(eastern)

            try:
                result_set = build.get_resultset()
            except:
                continue

            tests = result_set.items()

            build_url = build._data['url']
            report_url = ''
            if build_url[-1:] in '/':
                report_url += build_url + 'allure'
            else:
                report_url += build_url + '/allure'
            # формируем данные по билду
            data = {
                'job_name': job_name,
                'name': str(build._data['fullDisplayName']),
                'url': report_url,
                'start_time': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp': timestamp.timestamp(),
                'status': build.get_status(),
                'duration': str(datetime.timedelta(seconds=build.get_duration().seconds)),
                'results': {key: str(result_set._data[key]) for key in result_set._data if 'Count' in key},
                'tests': [{
                    'testName': item[0].split('.')[-2:][0] + ' -> ' + item[0].split('.')[-2:][1].replace("_", " "),
                    'age': item[1].age,
                    'className': item[1].className,
                    'name': item[1].name,
                    'status': item[1].status
                } for item in tests]
            }

            # формируем сообщения
            telegram_message = make_telegram_message(data)
            slack_message = make_slack_message(data)

            # отправляем бродкастеру
            broadcaster.send_telegram(telegram_message, view_type)
            broadcaster.send_slack(slack_message, view_type)

            last_time[job_name] = timestamp


def get_fresh_tests(data):
    """
    Находим свежие упавшие тесты, если упали меньше 10 раз подряд

    :param data:данные по билду
    :return:  список свежих упавших тестов
    """

    fresh = []
    for test in data['tests']:
        if 0 < test['age'] < 10 and test['status'] not in ('PASSED', 'SKIPPED'):
            fresh.append(test)
    return fresh


def make_telegram_message(data):
    """
    Формируем сообщение для телеграма с краткой информацией по билду

    :param data: данные по билду
    :return:  готовое сообщение
    """
    message = '''[{job_name}]({url})
Status: *{status}*
Start time: {start}
Duration: {duration}

*Tests:*
Total: {total}
Skipped: {skipped}
Failed: {failed}
    '''.format(job_name=data['name'],
               url=data['url'],
               status=data['status'],
               start=data['start_time'],
               duration=data['duration'],
               total=data['results']['totalCount'],
               skipped=data['results']['skipCount'],
               failed=data['results']['failCount'])
    fresh = get_fresh_tests(data)
    # если появились свежие непрошедшие тесты, то включаем в отчет
    if len(fresh) > 0:
        message += '\nFresh failed tests:\n'
        for item in fresh[:10]:
            fresh_test = item['testName'] + ' - ' + str(item['age']) + ' tms\n'
            if len(message + fresh_test) < 4096:
                message += fresh_test
            else:
                message += ' and more...'
                return message
        if len(fresh) > 10:
            message += ' and more...'
    return message


def make_slack_message(data):
    """
    Формируем сообщение для слака с краткой информацией по билду

    :param data: данные по билду
    :return: готовое сообщение
    """
    main_info = {'title': data['name'],
                 'title_link': data['url'],
                 'timestamp': data['timestamp'],
                 'text': '''Status: {status}
Start time: {start}
Duration: {duration}'''
                     .format(status=data['status'],
                             start=data['start_time'],
                             duration=data['duration']),
                 'color': colors[data['status']]}
    fresh = get_fresh_tests(data)
    # если появились свежие непрошедшие тесты, то включаем в отчет

    fresh_test = '''
Total: {total}
Skipped: {skipped}
Failed: {failed}

'''.format(
        total=data['results']['totalCount'],
        skipped=data['results']['skipCount'],
        failed=data['results']['failCount'])
    for item in fresh:
        fresh_test += item['testName'] + ' - ' + str(item['age']) + ' tms\n'
    detail_info = {
        'title': 'Tests:',
        'text': fresh_test,
        'color': colors['DETAIL']
    }
    return [main_info, detail_info]


while True:
    try:
        jenkins_request()
        jenkins_request(view_type="debug")
    except:
        print('Oops')
        pass
    time.sleep(20)
