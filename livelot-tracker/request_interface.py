import requests
import logging
logger = logging.getLogger('livelot-tracker.car_tracker')

# moved this out of the actual request if we ever change where the api is hosted
requestURL = 'https://livelotapi.herokuapp.com'

def carIn(lotId):
	try:
		response = requests.put(requestURL + '/lot/{}/carIn'.format(lotId))
		if response.status_code is not 200:
			logger.error(response.json())
		else:
			logger.info('Car Entered')
			logger.info(response.json())
	except Exception as e:
		logger.error(str(e))

def carOut(lotId):
	try:
		response = requests.put(requestURL + '/lot/{}/carOut'.format(lotId))
		if response.status_code is not 200:
			logger.error(response.json())
		else:
			logger.info('Car Exited')
			logger.info(response.json())
	except Exception as e:
		logger.error(str(e))