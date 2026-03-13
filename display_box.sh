#!/bin/bash

# Shell脚本显示框示例
# 支持多种样式的文本框

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 函数：打印单行框
print_single_box() {
    local text="$1"
    local width=${2:-50}
    local padding=$(( (width - ${#text}) / 2 ))
    
    echo -n "${CYAN}"
    for ((i=0; i<width; i++)); do echo -n "-"; done
    echo "${NC}"
    
    echo -n "${CYAN}|${NC}"
    printf "%*s" $padding ""
    echo -n "${WHITE}${text}${NC}"
    printf "%*s" $((width - padding - ${#text} - 1)) ""
    echo -n "${CYAN}|${NC}"
    echo ""
    
    echo -n "${CYAN}"
    for ((i=0; i<width; i++)); do echo -n "-"; done
    echo "${NC}"
}

# 函数：打印双线框
print_double_box() {
    local text="$1"
    local width=${2:-50}
    local padding=$(( (width - ${#text}) / 2 ))
    
    echo -n "${GREEN}"
    for ((i=0; i<width; i++)); do echo -n "="; done
    echo "${NC}"
    
    echo -n "${GREEN}|${NC}"
    printf "%*s" $padding ""
    echo -n "${WHITE}${text}${NC}"
    printf "%*s" $((width - padding - ${#text} - 1)) ""
    echo -n "${GREEN}|${NC}"
    echo ""
    
    echo -n "${GREEN}"
    for ((i=0; i<width; i++)); do echo -n "="; done
    echo "${NC}"
}

# 函数：打印星形框
print_star_box() {
    local text="$1"
    local width=${2:-50}
    local padding=$(( (width - ${#text}) / 2 ))
    
    echo -n "${YELLOW}"
    for ((i=0; i<width; i++)); do echo -n "*"; done
    echo "${NC}"
    
    echo -n "${YELLOW}*${NC}"
    printf "%*s" $padding ""
    echo -n "${WHITE}${text}${NC}"
    printf "%*s" $((width - padding - ${#text} - 1)) ""
    echo -n "${YELLOW}*${NC}"
    echo ""
    
    echo -n "${YELLOW}"
    for ((i=0; i<width; i++)); do echo -n "*"; done
    echo "${NC}"
}

# 函数：打印井号框
print_hash_box() {
    local text="$1"
    local width=${2:-50}
    local padding=$(( (width - ${#text}) / 2 ))
    
    echo -n "${PURPLE}"
    for ((i=0; i<width; i++)); do echo -n "#"; done
    echo "${NC}"
    
    echo -n "${PURPLE}#${NC}"
    printf "%*s" $padding ""
    echo -n "${WHITE}${text}${NC}"
    printf "%*s" $((width - padding - ${#text} - 1)) ""
    echo -n "${PURPLE}#${NC}"
    echo ""
    
    echo -n "${PURPLE}"
    for ((i=0; i<width; i++)); do echo -n "#"; done
    echo "${NC}"
}

# 函数：打印信息框（多行）
print_info_box() {
    local title="$1"
    local content="$2"
    local width=${3:-60}
    
    # 标题行
    echo -n "${BLUE}"
    for ((i=0; i<width; i++)); do echo -n "═"; done
    echo "${NC}"
    
    # 标题内容
    local title_padding=$(( (width - ${#title} - 2) / 2 ))
    echo -n "${BLUE}║${NC}"
    printf "%*s" $title_padding ""
    echo -n "${YELLOW}${title}${NC}"
    printf "%*s" $((width - title_padding - ${#title} - 2)) ""
    echo -n "${BLUE}║${NC}"
    echo ""
    
    # 分隔线
    echo -n "${BLUE}║${NC}"
    for ((i=0; i<width-2; i++)); do echo -n "─"; done
    echo -n "${BLUE}║${NC}"
    echo ""
    
    # 内容行
    while IFS= read -r line; do
        echo -n "${BLUE}║${NC}"
        echo -n " ${WHITE}${line}${NC}"
        printf "%*s" $((width - ${#line} - 3)) ""
        echo -n "${BLUE}║${NC}"
        echo ""
    done <<< "$content"
    
    # 底部边框
    echo -n "${BLUE}"
    for ((i=0; i<width; i++)); do echo -n "═"; done
    echo "${NC}"
}

# 函数：打印警告框
print_warning_box() {
    local text="$1"
    local width=${2:-50}
    
    echo -n "${RED}"
    for ((i=0; i<width; i++)); do echo -n "!"; done
    echo "${NC}"
    
    echo -n "${RED}!${NC} ${YELLOW}WARNING:${NC} ${WHITE}${text}${NC}"
    echo ""
    
    echo -n "${RED}"
    for ((i=0; i<width; i++)); do echo -n "!"; done
    echo "${NC}"
}

# 函数：打印成功框
print_success_box() {
    local text="$1"
    local width=${2:-50}
    
    echo -n "${GREEN}"
    for ((i=0; i<width; i++)); do echo -n "✓"; done
    echo "${NC}"
    
    echo -n "${GREEN}✓${NC} ${WHITE}SUCCESS:${NC} ${GREEN}${text}${NC}"
    echo ""
    
    echo -n "${GREEN}"
    for ((i=0; i<width; i++)); do echo -n "✓"; done
    echo "${NC}"
}

# 主函数：演示所有样式
main() {
    clear
    echo ""
    
    # 演示各种样式
    print_single_box "单线框示例" 40
    echo ""
    
    print_double_box "双线框示例" 40
    echo ""
    
    print_star_box "星形框示例" 40
    echo ""
    
    print_hash_box "井号框示例" 40
    echo ""
    
    print_info_box "信息框" "这是一个多行信息框示例
可以显示多行内容
适合用于显示详细信息" 50
    echo ""
    
    print_warning_box "这是一个警告消息" 40
    echo ""
    
    print_success_box "操作成功完成" 40
    echo ""
    
    # 交互式示例
    echo -e "${CYAN}选择显示框样式:${NC}"
    echo "1. 单线框"
    echo "2. 双线框"
    echo "3. 星形框"
    echo "4. 井号框"
    echo "5. 信息框"
    echo "6. 警告框"
    echo "7. 成功框"
    echo "8. 全部显示"
    read -p "请输入选择 (1-8): " choice
    
    case $choice in
        1) print_single_box "你选择了单线框" ;;
        2) print_double_box "你选择了双线框" ;;
        3) print_star_box "你选择了星形框" ;;
        4) print_hash_box "你选择了井号框" ;;
        5) print_info_box "信息框" "这是用户选择的信息框内容" ;;
        6) print_warning_box "这是一个警告示例" ;;
        7) print_success_box "操作成功！" ;;
        8) main ;; # 重新显示全部
        *) echo "无效选择" ;;
    esac
}

# 如果直接运行脚本，执行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
