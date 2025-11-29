#!/usr/bin/env python3
"""示例脚本"""

import sys
import json

def main():
    """主函数"""
    # 获取命令行参数
    args = sys.argv[1:]
    
    # 处理逻辑
    result = {
        "status": "success",
        "args": args,
        "message": "脚本执行成功"
    }
    
    # 输出 JSON 格式结果
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

