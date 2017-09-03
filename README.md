# Бот для публикации результатов прогона тестов

- python 3.5
- requests

### Workflow:

- идем на апи дженкинса
- заходим в нужно вью
- проходимся по всем билдам на вью
- если время старта последнего билда больше записанного в списке зпаусков то достаем все данные из последнего уадачного прогона билда
- парсим данные, достаем результаты тестов, преобразуем в удовлетворит вид
- формируем сообщения для слака и телеграма
- посылаем необходимые каналы 
- спим 20 секунд

# Как запускать:
```bash
./build.sh
docker run --name bot report_bot:latest
```

##### Локально:

```bash
pip install -r requirements.txt   
python src/reporter
```
