import base64
import imp
import io
import json

import dash_dangerously_set_inner_html
import json2html
from deepdiff import DeepDiff
import pandas as pd
import dash

from dash import html, dcc
from dash.dependencies import Input, Output, State

app = dash.Dash()
# df=get_diff_of_two_dataset()
old_df = None
new_df = None
app.layout = html.Div([  # this code section taken from Dash docs https://dash.plotly.com/dash-core-components/upload
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Old Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
    html.Div(id='output-div'),
    html.Div(id='output-datatable'),


])


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')
    df=pd.DataFrame()
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    df['filename']=filename
    return df.fillna("").to_dict(orient='records')

@app.callback(Output('output-datatable', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        old_df=pd.DataFrame()
        new_df=pd.DataFrame()
        i=0
        for df in children:
            df=pd.DataFrame(df)
            if 'generic' not in df.loc[0,'filename']:
                if i == 0:
                    old_df = df.fillna("")
                    i = i + 1
                else:
                    old_df = pd.concat(old_df, df).fillna("")
                    old_df.fillna("").to_dict('records')
            else:
                new_df=df
        old_df=old_df.drop(['filename'],axis=1)
        new_df = new_df.drop(['filename'],axis=1)
        old_transactionid_list = old_df['read_id'].to_list()
        new_transactionid_list = new_df['read_id'].to_list()
        # find old transactionlist have but not in new transaction list
        not_present_new_list = []
        extra_present_new_list = []
        for old_transaction_id in old_transactionid_list:
            if old_transaction_id not in new_transactionid_list:
                not_present_new_list.append(old_transaction_id)
        for new_transaction_id in new_transactionid_list:
            if new_transaction_id not in old_transactionid_list:
                extra_present_new_list.append(new_transaction_id)
        list_to_print=[]

        print('not present in new architecture ')
        list_to_print.append(html.P('not present in new architecture'))

        print(not_present_new_list)

        list_to_print.append(html.P(str(not_present_new_list)))
        list_to_print.append(html.Hr())

        print('extra present in new architecture')

        list_to_print.append(html.P('extra present in new architecture'))
        print(extra_present_new_list)
        list_to_print.append(html.P(str(extra_present_new_list)))
        list_to_print.append(html.Hr())

        common_list = list(set(old_transactionid_list).intersection(new_transactionid_list))
        for id in common_list:
            old_df_row = old_df.loc[old_df['read_id'] == id].to_dict(orient='records')
            new_df_row = new_df.loc[new_df['read_id'] == id].to_dict(orient='records')
            result = DeepDiff(old_df_row, new_df_row)
            if 'values_changed' in result:
                print("read_id " + str(id))
                list_to_print.append(html.P("read_id " + str(id)))
                data_dict=result['values_changed']
                keysList = list(data_dict.keys())
                for key in keysList:
                    data_dict[key.replace('root[0]','')] = data_dict.pop(key)
                print(data_dict)
                datar = json.dumps(data_dict)
                print(datar)
                jsonhtml = json2html.json2html.convert(json=datar)
                list_to_print.append(dash_dangerously_set_inner_html.DangerouslySetInnerHTML(jsonhtml))
                list_to_print.append(html.Hr())



        return html.Div(list_to_print)


if __name__ == '__main__':
    app.run_server(debug=True)