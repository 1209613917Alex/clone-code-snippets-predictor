import datetime
import xml.dom.minidom as minidom
from pydriller import Repository


def get_commit(save_name, rep_url, start_date, end_date):
    try:
        dom = minidom.getDOMImplementation().createDocument(None, 'Root', None)  # 创建树
        root = dom.documentElement  # 创建root节点

        parse_repeat_commit = []  # 用于提交去重

        # 根据时间进行划分，直接使用远程仓库URL
        rep = Repository(rep_url,
                         since=start_date,
                         to=end_date,
                         include_remotes=False).traverse_commits()
        for commit in rep:
            commit_msg = commit.msg  # 获取提交描述
            commit_date = commit.committer_date  # 获取提交日期
            print(commit_date)
            author = commit.author.name  # 获取提交作者
            if [commit_msg, commit_date] in parse_repeat_commit:
                continue  # 筛去重复提交
            else:
                parse_repeat_commit.append([commit_msg, commit_date])

            # 筛出C++、C源文件与头文件
            try:
                files = commit.modified_files  # 获取此次提交修改的文件列表
                commit_files = []  # 筛选出修改的C++、C头文件和源文件
                commit_names = []  # 筛选出的文件路径
                for file in files:
                    if file.old_path and (
                            '.cc' in file.old_path or '.cpp' in file.old_path or '.h' in file.old_path or '.c' in file.old_path):
                        commit_files.append(file)  # 将涉及了C++、C文件和头文件的提交文件存储
                        commit_names.append(file.old_path)  # 将该文件路径加入到列表中
                if not len(commit_files) > 0:  # 如果当前提交中不包含C++、C源文件和头文件的修改就跳过
                    continue
            except Exception as e:
                print(f"Error processing commit {commit.hash}: {e}")
                continue

            # xml写入
            root_element = dom.createElement('commit')  # 提交信息的父节点
            root_element.setAttribute('hash', commit.hash)  # 提交的哈希值
            root_element.setAttribute('author', author)  # 提交的作者
            add_text_element(dom, root_element, commit_msg, 'msg')  # 添加描述信息的节点

            files_element = dom.createElement('modified_files')  # 改变文件信息的节点

            # 将提交文件信息写入XML文件
            for file in commit_files:
                file_element = dom.createElement('file')  # 单条改变文件信息的节点
                old_path = file.old_path
                new_path = file.new_path
                file_element.setAttribute('old_path', old_path)  # 旧文件路径
                file_element.setAttribute('new_path', new_path)  # 新文件路径

                # 添加增删行数信息
                added_lines = file.added_lines
                deleted_lines = file.deleted_lines
                file_element.setAttribute('added_lines', str(added_lines))
                file_element.setAttribute('deleted_lines', str(deleted_lines))

                diff = file.diff  # 该文件的差异内容
                add_text_element(dom, file_element, diff, 'diff')  # 添加差异信息的节点
                files_element.appendChild(file_element)  # 将单条文件信息添加到文件信息的节点上
            root_element.appendChild(files_element)  # 将文件信息添加到该条提交节点上
            root.appendChild(root_element)  # 将提交信息节点添加到文档父节点上

        with open(save_name, 'w', encoding='utf-8') as f:
            dom.writexml(f, addindent='\t', newl='\n', encoding='utf-8')
    except Exception as e:
        print(f"An error occurred while accessing the repository: {e}")


def add_text_element(dom, root_element, text, element_name):  # 用于添加需要的文本节点
    element = dom.createElement(element_name)  # 生成相应的节点
    element.appendChild(dom.createTextNode(text))  # 添加加入节点的文本
    root_element.appendChild(element)  # 在父节点加入这个文本节点


if __name__ == '__main__':
    rep_url = input('please input your repository:')
    # rep_url = 'D:\\download\\apollo-5.0.0\\apollo-5.0.0'  # 仓库URL
    # change the time range you want to extract:
    time_ranges = [
        (datetime.datetime(2019,1,8), datetime.datetime(2019,6,28))
    ]  # 时间范围列表

    for start_date, end_date in time_ranges:
        save_name = f'apollo_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}_commit.xml'  # 提交存储的位置
        get_commit(save_name, rep_url, start_date, end_date)
