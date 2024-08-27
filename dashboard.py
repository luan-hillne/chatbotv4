import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import gradio as gr
from collections import Counter
import re
from utils.db_postgresql import DatabaseHandler

# Tạo các biểu đồ để hiển thị trên dashboard

db_handler = DatabaseHandler()
df = db_handler.craw_data()
print(df)
def parse_date(date_str):
    if '_' in date_str:
        return pd.to_datetime(date_str, format="%Y-%m-%d_%H:%M:%S")

    else:
        return pd.to_datetime(date_str + "_00:00:00", format="%Y-%m-%d_%H:%M:%S")
    
df['created_date'] = df['created_date'].apply(parse_date)
# df1 = df[['user_id', 'created_date', 'input_type','error_code', 'human', 'ai']]
# Chuyển đổi cột created_date thành kiểu dữ liệu datetime
# df['created_date'] = pd.to_datetime(df['created_date'], format="%Y-%m-%d_%H:%M:%S")
print(df)
# 1. Number User theo Day
daily_user_count = df.groupby(df['created_date'].dt.date)['user_id'].nunique().reset_index()
daily_user_count.columns = ['Day', 'Number User']

# 2. Number User theo Month
monthly_user_count = df.groupby(df['created_date'].dt.to_period('M'))['user_id'].nunique().reset_index()
monthly_user_count['Day'] = monthly_user_count['created_date'].dt.to_timestamp()
monthly_user_count.columns = ['Month', 'Number User', 'Day']

# Nhóm dữ liệu theo Month và input_type
monthly_input_type_count = df.groupby([df['created_date'].dt.to_period('M'), 'input_type']).size().reset_index(name='Number')
monthly_input_type_count['Month'] = monthly_input_type_count['created_date'].dt.to_timestamp()
monthly_input_type_count = monthly_input_type_count.sort_values(by='Number', ascending=False)

# Hàm để lấy các từ xuất hiện nhiều nhất
def get_most_common_words(text_series, top_n=50):
    words = ' '.join(text_series.dropna()).lower()
    words = re.findall(r'\b\w+\b', words)
    word_counts = Counter(words)
    return word_counts.most_common(top_n)

most_common_words = get_most_common_words(df['human'])
words_df = pd.DataFrame(most_common_words, columns=['Word', 'Frequency'])

# Hàm tạo biểu đồ
def create_plots():
    fig, axs = plt.subplots(2, 2, figsize=(25, 15))

    # Biểu đồ Number User theo Day
    sns.barplot(x='Day', y='Number User', data=daily_user_count, palette='viridis', ax=axs[0, 0])
    axs[0, 0].set_title('Number user of day')
    axs[0, 0].set_xlabel('Day')
    axs[0, 0].set_ylabel('Number User')
    axs[0, 0].tick_params(axis='x', rotation=45)

    # Biểu đồ Number User theo Month
    sns.barplot(x='Day', y='Number User', data=monthly_user_count, palette='viridis', ax=axs[0, 1])
    axs[0, 1].set_title('Number user of month')
    axs[0, 1].set_xlabel('Month')
    axs[0, 1].set_ylabel('Number User')
    axs[0, 1].tick_params(axis='x', rotation=45)

    # Biểu đồ Number theo từng Input Type và Month
    palette = {
        'image': 'blue',
        'text': 'orange',
        'first_text': 'red',
        'voice': 'green',
        'inventory': 'purple',
        'similarity': 'brown',
    }
    plt.subplots_adjust(hspace=0.4, wspace=0.3)
    bar_plot = sns.barplot(x='Month', y='Number', hue='input_type', data=monthly_input_type_count, palette=palette, ax=axs[1, 0])
    axs[1, 0].set_title('Number type input')
    axs[1, 0].set_xlabel('Month')
    axs[1, 0].set_ylabel('Number')
    axs[1, 0].tick_params(axis='x', rotation=45)
    for p in bar_plot.patches:
        height = p.get_height()
        bar_plot.annotate(format(height, '.0f'),
                          (p.get_x() + p.get_width() / 2., height),
                          ha='center', va='center',
                          xytext=(0, 9),
                          textcoords='offset points')

    # Biểu đồ 50 từ xuất hiện nhiều nhất
    sns.barplot(x='Frequency', y='Word', data=words_df, ax=axs[1, 1])
    axs[1, 1].set_title('50 words used in human')
    axs[1, 1].set_xlabel('Number words')
    axs[1, 1].set_ylabel('Word')

    # Hiển thị bảng dữ liệu
    # Lưu biểu đồ vào một đối tượng Image
    plt.tight_layout()
    plt.savefig('/tmp/dashboard_plots.png')
    plt.close()
    return '/tmp/dashboard_plots.png'

df1 = df.copy()
df1 = df[['user_id', 'created_date', 'input_type', 'error_code', 'human', 'ai']]

def filter_records(df1, input_type):
    # Lọc các bản ghi dựa trên loại đầu vào
    if input_type:
        filtered_df = df1[df1['input_type'] == input_type]
    else:
        filtered_df = df1  # Nếu không chọn loại đầu vào, trả về toàn bộ DataFrame
    
    # Sắp xếp theo ngày mới nhất
    return filtered_df.sort_values(by='created_date', ascending=False)
    


def gradio_interface():
    with gr.Blocks() as demo:
        gr.Markdown("### Data Dashboard and Data Table")

        with gr.Row():
            with gr.Column():
                gr.Markdown("#### Visualization Dashboard")
                plot_image = gr.Image(
                    create_plots, 
                    type='filepath', 
                    label="Dashboard"
                )

        with gr.Row():
            with gr.Column():
                gr.Markdown("#### Filtered Data Table")
                
                # Các widget đầu vào
                input_type_dropdown = gr.Dropdown(
                    choices=[""] + df['input_type'].unique().tolist(), 
                    label="Select input type", 
                    value=""
                )
                data_table = gr.Dataframe(
                    headers=["user_id", "created_date", "input_type", "error_code", "human", "ai"],
                    datatype=["str", "date", "str", "str", "str", "str"],
                    row_count=10,  # Hiển thị nhiều dòng hơn
                    col_count=(6, "fixed"),
                    value=df[['user_id', 'created_date', 'input_type', 'error_code', 'human', 'ai']].values.tolist(),  
                )

                def update_data_table(input_type):
                    filtered_df = filter_records(df[['user_id', 'created_date', 'input_type', 'error_code', 'human', 'ai']], input_type)
                    return filtered_df

                # Cập nhật bảng dữ liệu khi có thay đổi trong dropdown
                input_type_dropdown.change(fn=update_data_table, inputs=input_type_dropdown, outputs=data_table)

        return demo
    
# Khởi chạy giao diện Gradio với IP và cổng cụ thể
if __name__ == "__main__":
    interface = gradio_interface()
    interface.launch()
