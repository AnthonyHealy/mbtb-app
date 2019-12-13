from rest_framework import status
from rest_framework.test import APITestCase, force_authenticate, APIClient
from .models import PrimeDetails, NeuropathologicalDiagnosis, TissueTypes, AutopsyTypes, OtherDetails
from .models import AdminAccount
from .serializers import PrimeDetailsSerializer, OtherDetailsSerializer, FileUploadPrimeDetailsSerializer, \
    FileUploadOtherDetailsSerializer, InsertRowPrimeDetailsSerializer
import jwt
import csv
import os


# This class is to set up test data
class SetUpTestData(APITestCase):

    @classmethod
    def setUpClass(cls):
        cls.tissue_type_1 = TissueTypes.objects.create(tissue_type="brain")
        cls.neuro_diagnosis_1 = NeuropathologicalDiagnosis.objects.create(neuro_diagnosis_name="Mixed AD VAD")
        cls.autopsy_type_1 = AutopsyTypes.objects.create(autopsy_type="Brain")
        cls.prime_details_1 = PrimeDetails.objects.create(
            neuro_diagnosis_id=cls.neuro_diagnosis_1, tissue_type=cls.tissue_type_1, mbtb_code="BB99-101",
            sex="Female", age="92", postmortem_interval="15", time_in_fix="10", preservation_method='Fresh Frozen',
            storage_year="2018-06-06T03:03:03", archive="No", clinical_diagnosis='test'
        )
        cls.other_details_1 = OtherDetails.objects.create(
            prime_details_id=cls.prime_details_1, autopsy_type=cls.autopsy_type_1, race='test',
            duration=123, clinical_details='test', cause_of_death='test', brain_weight=123,
            neuropathology_summary='test', neuropathology_gross='test', neuropathology_microscopic='test',
            cerad='', abc='', khachaturian='', braak_stage='test',
            formalin_fixed=True, fresh_frozen=True,
        )
        cls.test_data = {
            'mbtb_code': 'BB99-102', 'sex': 'Male', 'age': '70', 'postmortem_interval': '12',
            'time_in_fix': 'Not known', 'tissue_type': 'Brain', 'preservation_method': 'Fresh Frozen',
            'autopsy_type': 'Brain', 'neuropathology_diagnosis': "Mixed AD VAD", 'race': '',
            'clinical_diagnosis': 'AD', 'duration': 0, 'clinical_details': 'AD', 'cause_of_death': '',
            'brain_weight': 1080, 'neuropathology_summary': 'AD SEVERE WITH ATROPHY, NEURONAL LOSS AND GLIOSIS',
            'neuropathology_gross': '', 'neuropathology_microscopic': '', 'cerad': '', 'braak_stage': '',
            'khachaturian': '30', 'abc': '', 'formalin_fixed': 'True', 'fresh_frozen': 'True',
            'storage_year': '2018-06-06 03:03:03'
        }
        cls.file_upload_data = cls.test_data.copy()
        cls.file_upload_data['mbtb_code'] = 'BB99-103'

        # prime_details and other_details data with error in datatype
        cls.prime_details_error = cls.file_upload_data.copy()
        cls.other_details_error = cls.file_upload_data.copy()
        cls.missing_fields_error = cls.file_upload_data.copy()
        cls.changed_column_names = cls.file_upload_data.copy()
        cls.prime_details_error['storage_year'] = ''
        cls.other_details_error['duration'] = None
        del cls.missing_fields_error['duration']
        cls.changed_column_names['durations'] = cls.changed_column_names.pop('duration')

        # Creating csv files for FileUploadAPIViewTest
        cls.dict_to_csv_file(cls, 'file_upload_test.csv', cls.file_upload_data)
        cls.dict_to_csv_file(cls, 'file_upload_test.txt', cls.file_upload_data)
        cls.dict_to_csv_file(cls, 'prime_details_error.csv', cls.prime_details_error)
        cls.dict_to_csv_file(cls, 'other_details_error.csv', cls.other_details_error)
        cls.dict_to_csv_file(cls, 'empty_file.csv', {})
        cls.dict_to_csv_file(cls, 'missing_fields.csv', cls.missing_fields_error)
        cls.dict_to_csv_file(cls, 'changed_column_names.csv', cls.changed_column_names)

        # Admin Authentication: generate temp account and token
        cls.email = 'admin@mbtb.ca'
        cls.password = 'asdfghjkl123'
        AdminAccount.objects.create(email=cls.email, password_hash=cls.password)
        admin = AdminAccount.objects.get(email=cls.email)
        payload = {
            'id': admin.id,
            'email': admin.email,
        }
        cls.token = jwt.encode(payload, "SECRET_KEY", algorithm='HS256')  # generating jwt token
        cls.client = APIClient(enforce_csrf_checks=True)  # enforcing csrf checks

    # Create CSV file once filename and data is provided
    def dict_to_csv_file(self, filename, data):
        with open(filename, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=data.keys())
            writer.writeheader()
            writer.writerow(data)

    @classmethod
    def tearDownClass(cls):
        OtherDetails.objects.all().delete()
        PrimeDetails.objects.filter().delete()
        TissueTypes.objects.filter().delete()
        NeuropathologicalDiagnosis.objects.filter().delete()
        AutopsyTypes.objects.filter().delete()
        AdminAccount.objects.all().delete()
        os.remove('file_upload_test.csv')  # Removing csv files
        os.remove('prime_details_error.csv')
        os.remove('other_details_error.csv')
        os.remove('file_upload_test.txt')
        os.remove('empty_file.csv')
        os.remove('missing_fields.csv')
        os.remove('changed_column_names.csv')


# This class is to test PrimeDetailsAPIView: all request
# Default: only GET request is allowed with auth_token, remaining is blocked
class PrimeDetailsViewTest(SetUpTestData):

    def setUp(cls):
        super(SetUpTestData, cls).setUpClass()

    # get request with valid token
    def test_get_all_brain_dataset(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        response = self.client.get('/brain_dataset/')
        model_response = PrimeDetails.objects.all()
        serializer_response = PrimeDetailsSerializer(model_response, many=True)
        self.assertEqual(response.data, serializer_response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials()

    # get request without token
    def test_get_all_brain_dataset_invalid_request(self):
        response = self.client.get('/brain_dataset/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # get request for single brain_dataset with valid token and payload data
    def test_get_single_request(self):
        url = '/brain_dataset/' + str(self.prime_details_1.pk) + '/'
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        response = self.client.get(url)
        model_response = PrimeDetails.objects.get(pk=self.prime_details_1.pk)
        serializer_response = PrimeDetailsSerializer(model_response)
        self.assertEqual(response.data, serializer_response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials()

    # get request for single brain_dataset with valid token and invalid payload data
    def test_get_invalid_single_request(self):
        url = '/brain_dataset/' + '25' + '/'
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.client.credentials()

    # get request with empty token
    def test_get_with_empty_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + '')
        response_with_token = self.client.get('/brain_dataset/')
        self.assertEqual(response_with_token.status_code, status.HTTP_403_FORBIDDEN)

    # get request with invalid token header
    def test_invalid_token_header(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + ' get request with valid token')
        response_invalid_header = self.client.get('/brain_dataset/')
        self.assertEqual(response_invalid_header.status_code, status.HTTP_403_FORBIDDEN)

    # post request with and without token
    def test_post_request(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        response_with_token = self.client.post('/brain_dataset/1/')
        response_without_token = self.client.post('/brain_dataset/')
        self.assertEqual(response_with_token.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response_without_token.status_code, status.HTTP_403_FORBIDDEN)

    # delete request with and without token
    def test_delete_request(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        response_with_token = self.client.delete('/brain_dataset/1/')
        response_without_token = self.client.delete('/brain_dataset/')
        self.assertEqual(response_with_token.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response_without_token.status_code, status.HTTP_403_FORBIDDEN)

    def tearDown(cls):
        super(SetUpTestData, cls).tearDownClass()


# This class is to test OtherDetailsAPIView: all request
# Default: only GET request is allowed with auth_token, remaining is blocked
class OtherDetailsViewTest(SetUpTestData):

    def setUp(cls):
        super(SetUpTestData, cls).setUpClass()

    #  get request with valid token
    def test_get_all_othr_details(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        response = self.client.get('/other_details/')
        model_response = OtherDetails.objects.all()
        serializer_response = OtherDetailsSerializer(model_response, many=True)
        self.assertEqual(response.data, serializer_response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials()

    # get request without token
    def test_get_all_othr_details_invalid_request(self):
        response = self.client.get('/other_details/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # get request for single other_details with valid token and payload data
    def test_get_single_request(self):
        url = '/other_details/' + str(self.prime_details_1.pk) + '/'
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        response = self.client.get(url)
        model_response = OtherDetails.objects.get(pk=self.other_details_1.pk)
        serializer_response = OtherDetailsSerializer(model_response)
        self.assertEqual(response.data, serializer_response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials()

    # get request for single other_details with valid token and invalid payload data
    def test_get_invalid_single_request(self):
        url = '/other_details/' + '50' + '/'
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.client.credentials()

    # get request with empty token
    def test_get_with_empty_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + '')
        response_with_token = self.client.get('/other_details/')
        self.assertEqual(response_with_token.status_code, status.HTTP_403_FORBIDDEN)

    # get request with invalid token header
    def test_invalid_token_header(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + ' get request with valid token')
        response_invalid_header = self.client.get('/other_details/')
        self.assertEqual(response_invalid_header.status_code, status.HTTP_403_FORBIDDEN)

    # post request with and without token
    def test_post_request(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        response_with_token = self.client.post('/other_details/1/')
        response_without_token = self.client.post('/other_details/')
        self.assertEqual(response_with_token.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response_without_token.status_code, status.HTTP_403_FORBIDDEN)

    # delete request with and without token
    def test_delete_request(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        response_with_token = self.client.delete('/other_details/1/')
        response_without_token = self.client.delete('/other_details/')
        self.assertEqual(response_with_token.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response_without_token.status_code, status.HTTP_403_FORBIDDEN)

    def tearDown(cls):
        super(SetUpTestData, cls).tearDownClass()


# This class is to test CreateDataAPIView: all request
# Default: only POST request is allowed with auth_token, remaining is blocked
class CreateDataAPIViewTest(SetUpTestData):

    def setUp(cls):
        super(SetUpTestData, cls).setUpClass()

    # valid post request with token to insert data
    def test_insert_data_(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        response = self.client.post('/add_new_data/', self.test_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['Response'], 'Success')
        self.client.credentials()

        # Fetch prime_details and other_details for mbtb_code `BB99-103` and compare its length
        model_response_prime_details = PrimeDetails.objects.get(mbtb_code='BB99-102')
        model_response_other_details = OtherDetails.objects.get(
            prime_details_id=model_response_prime_details.prime_details_id
        )
        serializer_response_prime_details = InsertRowPrimeDetailsSerializer(model_response_prime_details)
        serializer_response_other_details = FileUploadOtherDetailsSerializer(model_response_other_details)
        set_test_data = set(self.test_data)
        set_prime_details = set(serializer_response_prime_details.data)
        set_other_details = set(serializer_response_other_details.data)
        self.assertEqual(len(set_prime_details.intersection(set_test_data)), 8)
        self.assertEqual(len(set_other_details.intersection(set_test_data)), 15)

    # post request without token
    def test_insert_data_without_token(self):
        response = self.client.post('/add_new_data/', self.test_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # post request with invalid data
    def test_invalid_data_check(self):
        self.test_data['mbtb_code'] = ''
        self.test_data['sex'] = ''
        self.test_data['duration'] = ''
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        response = self.client.post('/add_new_data/', self.test_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.client.credentials()

    # post request with invalid token header
    def test_invalid_token_header(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + 'get request with valid token')
        response_invalid_header = self.client.post('/add_new_data/', self.test_data, format='json')
        self.assertEqual(response_invalid_header.status_code, status.HTTP_403_FORBIDDEN)

    # post request with empty token
    def test_request_with_empty_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + '')
        response_with_token = self.client.post('/add_new_data/', self.test_data, format='json')
        self.assertEqual(response_with_token.status_code, status.HTTP_403_FORBIDDEN)

    def tearDown(cls):
        super(SetUpTestData, cls).tearDownClass()


# This class is to test GetSelectOptions: all request
# Default: only get request is allowed with auth_token, remaining is blocked
class GetSelectOptionsViewTest(SetUpTestData):

    def setUp(cls):
        super(SetUpTestData, cls).setUpClass()

        # Fetch following values: autopsy_type, tissue_type, neuropathology_diagnosis for comparison
        _neuropathology_diagnosis = NeuropathologicalDiagnosis.objects.values_list('neuro_diagnosis_name', flat=True) \
            .order_by('neuro_diagnosis_name')
        _autopsy_type = AutopsyTypes.objects.values_list('autopsy_type', flat=True).order_by('autopsy_type')
        _tissue_type = TissueTypes.objects.values_list('tissue_type', flat=True).order_by('tissue_type')
        cls.valid_response = {
            "neuropathology_diagnosis": _neuropathology_diagnosis,
            "autopsy_type": _autopsy_type,
            "tissue_type": _tissue_type
        }

    # get request to fetch valid data
    def test_get_valid_data(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        response = self.client.get('/get_select_options/')
        self.assertQuerysetEqual(response.data, self.valid_response, transform=lambda x: x)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials()

    # get request without token
    def test_get_data_without_token(self):
        response = self.client.get('/get_select_options/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # get request with invalid token header
    def test_invalid_token_header(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + ' get request with invalid token')
        response_invalid_header = self.client.get('/get_select_options/')
        self.assertEqual(response_invalid_header.status_code, status.HTTP_403_FORBIDDEN)

    # get request with empty token
    def test_get_request_with_empty_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + '')
        response_with_token = self.client.get('/get_select_options/')
        self.assertEqual(response_with_token.status_code, status.HTTP_403_FORBIDDEN)

    # invalid post request test
    def test_post_request(self):
        response_without_token = self.client.post('/get_select_options/')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        response_with_token = self.client.post('/get_select_options/')
        self.assertEqual(response_with_token.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response_without_token.status_code, status.HTTP_403_FORBIDDEN)

    # invalid delete request test
    def test_delete_request(self):
        response_without_token = self.client.delete('/get_select_options/')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        response_with_token = self.client.delete('/get_select_options/')
        self.assertEqual(response_with_token.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response_without_token.status_code, status.HTTP_403_FORBIDDEN)

    def tearDown(cls):
        super(SetUpTestData, cls).tearDownClass()


# This class is to test FileUploadAPIView: all request
# Default: only post request is allowed with auth_token, remaining is blocked
class FileUploadAPIViewTest(SetUpTestData):

    def setUp(cls):
        super(SetUpTestData, cls).setUpClass()

    def test_data_upload(self):
        # Upload data and check status code and response
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        response = self.client.post(
            '/file_upload/', {'file': open('file_upload_test.csv', 'rb')}, headers={'Content-Type': 'text/csv'}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['Response'], 'Success')
        self.client.credentials()

        # Fetch prime_details and other_details for mbtb_code `BB99-103` and compare its length
        model_response_prime_details = PrimeDetails.objects.get(mbtb_code='BB99-103')
        model_response_other_details = OtherDetails.objects.get(
            prime_details_id=model_response_prime_details.prime_details_id
        )
        serializer_response_prime_details = FileUploadPrimeDetailsSerializer(model_response_prime_details)
        serializer_response_other_details = FileUploadOtherDetailsSerializer(model_response_other_details)
        set_file_upload_data = set(self.file_upload_data)
        set_prime_details = set(serializer_response_prime_details.data)
        set_other_details = set(serializer_response_other_details.data)
        self.assertEqual(len(set_prime_details.intersection(set_file_upload_data)), 9)
        self.assertEqual(len(set_other_details.intersection(set_file_upload_data)), 15)

    # post request without token
    def test_data_upload_without_token(self):
        predicted_msg = 'Authentication credentials were not provided.'
        response = self.client.post(
            '/file_upload/', {'file': open('file_upload_test.csv', 'rb')}, headers={'Content-Type': 'text/csv'}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], predicted_msg)
        self.client.credentials()

    # post request with invalid token
    def test_invalid_token_header(self):
        predicted_msg = 'Invalid token header'
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + ' get request with invalid token')
        response_invalid_header = self.client.post(
            '/file_upload/', {'file': open('file_upload_test.csv', 'rb')}, headers={'Content-Type': 'text/csv'}
        )
        self.assertEqual(response_invalid_header.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response_invalid_header.data['detail'], predicted_msg)

    # post request with empty token
    def test_request_with_empty_token(self):
        predicted_msg = 'Invalid token header. No credentials provided.'
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + '')
        response_with_token = self.client.post(
            '/file_upload/', {'file': open('file_upload_test.csv', 'rb')}, headers={'Content-Type': 'text/csv'}
        )
        self.assertEqual(response_with_token.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response_with_token.data['detail'], predicted_msg)

    # invalid data test with error in prime details
    def test_prime_details_error(self):
        predicted_msg = 'Error in prime details, Data uploading failed at mbtb_code: BB99-103'
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        response_prime_details_error = self.client.post(
            '/file_upload/', {'file': open('prime_details_error.csv', 'rb')}, headers={'Content-Type': 'text/csv'}
        )
        self.assertEqual(response_prime_details_error.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_prime_details_error.data['Response'], 'Failure')
        self.assertEqual(response_prime_details_error.data['Message'], predicted_msg)
        self.assertGreater(len(response_prime_details_error.data['Error']), 0)
        self.client.credentials()

    # invalid data test with error in other details
    def test_other_details_error(self):
        predicted_msg = 'Error in other details, Data uploading failed at mbtb_code: BB99-103'
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        response_other_details_error = self.client.post(
            '/file_upload/', {'file': open('other_details_error.csv', 'rb')}, headers={'Content-Type': 'text/csv'}
        )
        self.assertEqual(response_other_details_error.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_other_details_error.data['Response'], 'Failure')
        self.assertEqual(response_other_details_error.data['Message'], predicted_msg)
        self.assertGreater(len(response_other_details_error.data['Error']), 0)
        self.client.credentials()

    # test: without `file` tag or empty `file` tag
    def test_file_not_found(self):
        predicted_msg_1 = "File not found, please upload CSV file"
        predicted_msg_2 = "File can't be empty, Please upload again."
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        resposne_no_file_tag = self.client.post(
            '/file_upload/', {'no_file': open('file_upload_test.csv', 'rb')}, headers={'Content-Type': 'text/csv'}
        )
        response_empty_file_tag = self.client.post(
            '/file_upload/', {'file': ''}, headers={'Content-Type': 'text/csv'}
        )
        self.assertEqual(resposne_no_file_tag.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_empty_file_tag.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resposne_no_file_tag.data['Error'], predicted_msg_1)
        self.assertEqual(response_empty_file_tag.data['Error'], predicted_msg_2)
        self.client.credentials()

    def test_file_type(self):
        predicted_msg = 'Wrong file type, please upload CSV file'
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        resposne_no_file_extension = self.client.post(
            '/file_upload/', {'file': open('file_upload_test.txt', 'rb')}, headers={'Content-Type': 'text/csv'}
        )
        self.assertEqual(resposne_no_file_extension.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resposne_no_file_extension.data['Error'], predicted_msg)
        self.client.credentials()

    def test_file_size(self):
        predicted_msg_1 = 'Error in file size, please upload valid file.'
        predicted_msg_2 = 'Not enough elements are present in single row.'
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        resposne_empty_file = self.client.post(
            '/file_upload/', {'file': open('empty_file.csv', 'rb')}, headers={'Content-Type': 'text/csv'}
        )
        response_missing_data = self.client.post(
            '/file_upload/', {'file': open('missing_fields.csv', 'rb')}, headers={'Content-Type': 'text/csv'}
        )
        self.assertEqual(resposne_empty_file.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_missing_data.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resposne_empty_file.data['Error'], predicted_msg_1)
        self.assertEqual(response_missing_data.data['Error'], predicted_msg_2)
        self.client.credentials()

    def test_column_names(self):
        predicted_msg = "Column names don't match with following: ['duration'], Please try again with valid names."
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        resposne_changed_names = self.client.post(
            '/file_upload/', {'file': open('changed_column_names.csv', 'rb')}, headers={'Content-Type': 'text/csv'}
        )
        self.assertEqual(resposne_changed_names.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resposne_changed_names.data['Error'], predicted_msg)
        self.client.credentials()

    # invalid get request test
    def test_get_request(self):
        response_without_token = self.client.get(
            '/file_upload/', {'file': open('file_upload_test.csv', 'rb')}, headers={'Content-Type': 'text/csv'}
        )
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        response_with_token = self.client.get(
            '/file_upload/', {'file': open('file_upload_test.csv', 'rb')}, headers={'Content-Type': 'text/csv'}
        )
        self.assertEqual(response_with_token.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response_without_token.status_code, status.HTTP_403_FORBIDDEN)

    # invalid delete request test
    def test_delete_request(self):
        response_without_token = self.client.delete(
            '/file_upload/', {'file': open('file_upload_test.csv', 'rb')}, headers={'Content-Type': 'text/csv'}
        )
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.decode('utf-8'))
        response_with_token = self.client.delete(
            '/file_upload/', {'file': open('file_upload_test.csv', 'rb')}, headers={'Content-Type': 'text/csv'}
        )
        self.assertEqual(response_with_token.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response_without_token.status_code, status.HTTP_403_FORBIDDEN)

    def tearDown(cls):
        super(SetUpTestData, cls).tearDownClass()
