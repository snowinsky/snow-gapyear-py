import json
import unittest
from lenovo.promptshare.prompt_share_api import prompt_share_restapi

class TestDevPromptShare(unittest.TestCase):

    def setUp(self):
        self.api = prompt_share_restapi("http://localhost:8080")


    def test_prompt_list(self):
        ret = self.api.get_prompt_by_owner('4sadf', 'cn')
        print(ret)
        ret_obj = json.loads(ret)
        self.assertEqual(ret_obj['code'], 0)


    def test_prompt_share(self):
        share_ret = self.api.share_prompt('aaa@l.com', ['jigs2@lenovo.com'], [3], 'it maybe helpfull for u!!!!')
        print(share_ret)

    def test_prompt_delete(self):
        delete_ret = self.api.delete_prompt([1,2])
        print(delete_ret)




if __name__ == '__main__':
    unittest.main()