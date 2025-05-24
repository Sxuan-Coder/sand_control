from config.default_config import (mixture_sample_index, calculate_type, to_link,
    main_gradeNames, main_data_path, main_view, main_volume_corrections,
    main_LABELS, main_gradeEnabled)

import reader
import statistics
import numpy as np
import math
import normal5
import csv
import os
import datetime
from functools import reduce
from zsh_methods import get_mx, diameter_gap_average, area_gap, physics_gap

# 参与计算的标志
gradeEnabled = main_gradeEnabled
data_path = main_data_path
gradeNames = main_gradeNames
view = main_view
# distributions = main_distributions

LABELS = main_LABELS

volume_corrections = main_volume_corrections

volume_corrections = [a * b for a, b in zip(volume_corrections, gradeEnabled)]



def calculate_mean_and_variance(rawDistributions=None,show_figure=True):
    singleLocs ={}
    distributions = []
    datas=[]
    prop = "short_list"
    # prop = "long_list"
    # prop = "area_list"
    # prop = "volume_list"
    for j in range(0,len(gradeNames)):
        print("singleLoc:",gradeNames[j])
        # data =  reader.parse_txt_to_dict("/Users/chuanyunxu/Documents/DDD/workspace/Work/2025/09 砂级配/张世豪-砂级配实验数据/data_text/single/local/"+singleLoc+".txt")
        data =  reader.load_dict_from_file(data_path+"/single/"+str(gradeNames[j])+"/"+view+"/"+str(gradeNames[j])+".txt")
        # data =  reader.load_dict_from_file(data_path+"/single/"+view+ "/" +str(gradeNames[j])+".txt")
        if len(data)==0:
            distributions.append([0, 0,0])
            continue
        if show_figure:
            datas.append([item for sublist in data[prop] for item in sublist])
        # for imageIndex in range(5): 
        #     sum = 0
        #     cout = 0
        #     for i in range(imageIndex,len(data[prop]),5):
        #         sum += np.sum(data[prop][i])
        #         cout += len(data[prop][i])            
        #     print(sum/cout)
        sum = 0
        cout = 0
        varianceSum=0

        if distributions == None:
            for i in range(0,len(data[prop])):
                sum += np.sum(data[prop][i])
                cout += len(data[prop][i])    
            mean = sum/cout    
            for i in range(0,len(data[prop])):
                varianceSum += np.sum((x - mean)**2 for x in data[prop][i])
        else:
            normalRange=(rawDistributions[j][0]- rawDistributions[j][1]*1.5,rawDistributions[j][0] + rawDistributions[j][1]*1.5)
            for i in range(0,len(data[prop])):
                for v in data[prop][i]:
                    if v >= normalRange[0]  and v <=normalRange[1]  :                   
                        sum += v
                        cout += 1  
            mean = sum/cout    
            for i in range(0,len(data[prop])):
                for v in data[prop][i]:
                    if v >= normalRange[0]  and v <=normalRange[1]  :                  
                        varianceSum += (v - mean)**2 

        variance = varianceSum/cout

        distributions.append([mean, math.sqrt(variance),cout])


    # distributions = []
    # datas=[]
    if show_figure:   
        #  for sampleIndex in range(1,11):
        #     mean,std,cout,datas1 =calculate_sample_mean_and_variance(sampleIndex,show_figure)
        #     distributions.append([mean, std,cout])
        #     datas.append(datas1)      
         normal5.plot_histogram(datas,distributions, bins=200, title=f"Histogram of short_list for {gradeNames[j]}")

    return distributions
def calculate_sample_mean_and_variance(sampleIndex,show_figure=True):
    singleLocs ={}
    distributions = []
    datas=[]
    # prop = "long_list"
    # prop = "area_list"
    # prop = "volume_list"
    prop =  "l_short_list" if view=="local" else "g_short_list"
    sum = 0
    cout = 0
    varianceSum=0
    for fileIndex in range(1,100):
        file_path =fr"{data_path}/mixture/sample{sampleIndex}/value{fileIndex}.txt"
        if not os.path.exists(file_path):        
            break  
        data =  reader.load_dict_from_file(file_path) 
        # data =  reader.parse_txt_to_dict("/Users/chuanyunxu/Documents/DDD/workspace/Work/2025/09 砂级配/张世豪-砂级配实验数据/data_text/single/local/"+singleLoc+".txt")

        # for imageIndex in range(5): 
        #     sum = 0
        #     cout = 0
        #     for i in range(imageIndex,len(data[prop]),5):
        #         sum += np.sum(data[prop][i])
        #         cout += len(data[prop][i])            
        #     print(sum/cout)

        for i in range(0,len(data[prop])):
            sum += np.sum(data[prop][i])
            cout += len(data[prop][i])    
    mean = sum/cout    
    for fileIndex in range(1,100):
        file_path =fr"{data_path}/mixture/sample{sampleIndex}/value{fileIndex}.txt"
        if not os.path.exists(file_path):        
            break  
        data =  reader.load_dict_from_file(file_path) 

        if show_figure:
            datas=datas+[item for sublist in data[prop] for item in sublist]
    
        for i in range(0,len(data[prop])):
            varianceSum += np.sum((x - mean)**2 for x in data[prop][i])
    variance = varianceSum/cout
 
    return mean,math.sqrt(variance),cout,datas
def gen_grades_range_by_intersection(intersection_cdf_values,distributions,extendStdRatio=0):

    intersections = list(map(lambda x:x['intersection'],intersection_cdf_values))
    grades_ranges = []
    
    grades_ranges.append([0,intersections[0]+distributions[0][1]*extendStdRatio]) 
    for i in range(1,len(intersections)):
        grades_ranges.append([intersections[i-1]-distributions[i][1]*extendStdRatio, intersections[i]+distributions[i][1]*extendStdRatio])
    grades_ranges.append([intersections[-1]-distributions[-1][1]*extendStdRatio, 1000000000000]) # 添加一个最大值

    return grades_ranges


def compute_volume_percentage(grades_range,sampleIndex,batchInterval):
   
    def computeGrade(size,grades_range):
        sizeIndexes=[]
        for sizeIndex in range(0,len(grades_range)):
            if size>grades_range[sizeIndex][0] and size<=grades_range[sizeIndex][1]:
                sizeIndexes.append(sizeIndex)
        return sizeIndexes

    g_grades_range = []
    l_grades_range = grades_range
    for grade in l_grades_range:
        v1 = grade[0] / diameter_gap_average()
        v2 = grade[1] / diameter_gap_average()
        g_grades_range.append([v1,v2])

    prop =  "l_short_list" if view=="local" else "g_short_list"
    propArea =  "l_area_list" if view=="local" else "g_area_list"
    valumes=[[0,0,0,0,0,0] for i in range(0,batchInterval)]
    couts=[[0,0,0,0,0,0] for i in range(0,batchInterval)]

    valumes1 = [[0, 0, 0, 0, 0, 0] for i in range(0, batchInterval)]
    couts1 = [[0, 0, 0, 0, 0, 0] for i in range(0, batchInterval)]
    l_currentImageIndex=0
    g_currentImageIndex=0
    for fileIndex in range(1,100):
        file_path =fr"{data_path}/mixture{mixture_sample_index - 1}/sample{sampleIndex}/value{fileIndex}.txt"
        if not os.path.exists(file_path):        
            break  
        data =  reader.load_dict_from_file(file_path)  

        if to_link:
            for imageIndex in range(0, len(data[prop])):
                l_currentImageIndex += 1
                for particleIndex in range(0, len(data[prop][imageIndex])):
                    sizeIndexdes = computeGrade(data[prop][imageIndex][particleIndex], l_grades_range)
                    for sizeIndex in sizeIndexdes:
                        valumes[l_currentImageIndex % batchInterval - 1][sizeIndex] += data[prop][imageIndex][particleIndex] * data[propArea][imageIndex][particleIndex]
                        couts[l_currentImageIndex % batchInterval - 1][sizeIndex] += 1

            # todo 把全局的加上
            for imageIndex in range(0, len(data["g_short_list"])):
                g_currentImageIndex += 1
                for particleIndex in range(0, len(data["g_short_list"][imageIndex])):
                    sizeIndexdes = computeGrade(data["g_short_list"][imageIndex][particleIndex], g_grades_range)
                    for sizeIndex in sizeIndexdes:
                        valumes1[g_currentImageIndex % batchInterval - 1][sizeIndex] += data['g_short_list'][imageIndex][particleIndex] * data['g_area_list'][imageIndex][particleIndex]
                        couts1[g_currentImageIndex % batchInterval - 1][sizeIndex] += 1

            for t in range(batchInterval):
                for index in range(4,6):
                    valumes[t][index] = valumes1[t][index] * diameter_gap_average() * area_gap() / physics_gap()

        else:
            for imageIndex in range(0,len(data[prop])):
                l_currentImageIndex+=1
                for particleIndex in range(0,len(data[prop][imageIndex])):
                    sizeIndexdes = computeGrade(data[prop][imageIndex][particleIndex],grades_range)
                    for sizeIndex in sizeIndexdes:
                        valumes[l_currentImageIndex%batchInterval-1][sizeIndex]+= data[prop][imageIndex][particleIndex] * data[propArea][imageIndex][particleIndex]
                        couts[l_currentImageIndex%batchInterval-1][sizeIndex]+=1

    valumes =  [[volume*volume_correction  for volume,volume_correction in zip(valumes1,volume_corrections)] for valumes1 in valumes]
    total_volumes = [sum(valumes1) for valumes1 in valumes ] 
    volume_percentage = [[0 if total_volume==0 else volume1 / total_volume for volume1 in volume] for volume,total_volume in zip(valumes,total_volumes)]
    
    # 计算颗粒和体积通过率  
    particle_passing_rate = []
    volume_passing_rate = []
    
    if not calculate_type:
        # 使用0.15~4.75的标签范围进行通过率计算
        # 定义通过率计算用的标签列表 - 从0.15到4.75
        passing_grades = [0.15, 0.3, 0.6, 1.18, 2.36, 4.75]
        
        for batch_counts in couts:
            total_count = sum(batch_counts)
            # 计算颗粒通过率（累积百分比）
            passing = 0
            batch_passing = []
            for i in range(len(batch_counts)):
                passing += batch_counts[i]
                # 使用新的标签名
                batch_passing.append(0 if total_count == 0 else passing / total_count)
            particle_passing_rate.append(batch_passing)
        
        for batch_volumes in valumes:
            total_volume = sum(batch_volumes)
            # 计算体积通过率（累积百分比）
            passing = 0
            batch_passing = []
            for i in range(len(batch_volumes)):
                passing += batch_volumes[i]
                # 使用新的标签名
                batch_passing.append(0 if total_volume == 0 else passing / total_volume)
            volume_passing_rate.append(batch_passing)
    
    # print(volume_percentage)
    print(couts)
    if calculate_type:
        return volume_percentage, couts
    else:
        return volume_percentage, couts, particle_passing_rate, volume_passing_rate

def compute_volume_percentages(grades_range,batchInterval):
    volume_percentages =[]
    particle_counts = []
    particle_passing_rates = []
    volume_passing_rates = []
    
    for i in range(1,11):
       print("sample",i)
       if calculate_type:
           volume_percentage, counts = compute_volume_percentage(grades_range,i,batchInterval)
           volume_percentages.append(volume_percentage)
           particle_counts.append(counts)
       else:
           volume_percentage, counts, particle_passing, volume_passing = compute_volume_percentage(grades_range,i,batchInterval)
           volume_percentages.append(volume_percentage)
           particle_counts.append(counts)
           particle_passing_rates.append(particle_passing)
           volume_passing_rates.append(volume_passing)
           
    if calculate_type:
        return volume_percentages, particle_counts
    else:
        return volume_percentages, particle_counts, particle_passing_rates, volume_passing_rates

def computeDifferences(volume_percentages,LABELS,batchInterval):
    differences = []
    differences_sum = []

    for label,volume_percentages1 in zip(LABELS, volume_percentages):
        differences1 = []
        differences_sum1 = []
        for  volume_percentage in volume_percentages1:
            diff = map(lambda l,v: l - v ,label, volume_percentage)
            diff = list(diff)
            diff_diff_sum = reduce(lambda s,x:s+ abs(x),diff,0)
            differences1.append(diff)
            differences_sum1.append(diff_diff_sum)
        differences.append(differences1)
        differences_sum.append(differences_sum1)
    
    # 计算 differences 的均值
    mean_absolute_differences = [0] * batchInterval

    for differences_sum1 in differences_sum:
        for i in range(batchInterval):
            mean_absolute_differences[i] += differences_sum1[i]

    mean_absolute_differences = [a/len(LABELS) for a in mean_absolute_differences]
    
    return differences,differences_sum,mean_absolute_differences


def write_to_csv(LABELS, volume_percentages, differences, differences_sum, mean_absolute_differences, experiment_name,
                 batchInterval, mx, particle_counts):
    # print(f"Mean Absolute Difference({experiment_name}):", mean_absolute_difference)
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"result{mixture_sample_index - 1}/output_{current_time}_{view}_{experiment_name}_B{batchInterval}.csv"
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)

        # Write headers
        headers = ["Sample"] + [f"{x}_标签" for x in gradeNames] \
                  + [f"{x}_占比" for x in gradeNames] \
                  + [f"{x}_误差" for x in gradeNames] \
                  + [f"{x}_颗粒数" for x in gradeNames] \
                  + [f"汇总误差"] + ["细度模数(计算值)", "细度模数(标签值)", "细度模数误差"] \
                  + ["误差方差", "细度模数误差方差"]  # 新增的方差列
        writer.writerow(headers)

        for batch_index in range(0, batchInterval):
            # 计算当前批次的方差
            error_values = []
            mx_error_values = []
            
            for i in range(len(volume_percentages)):
                # 收集误差数据用于计算方差
                error_values.append(differences_sum[i][batch_index])
                
                # 收集细度模数误差数据
                if mx and batch_index < len(mx) and i < len(mx[batch_index]):
                    mx_error_values.append(mx[batch_index][i][0] - mx[batch_index][i][1])
                    
            for i in range(len(volume_percentages)):
                # 计算细度模数误差
                mx_error = mx[batch_index][i][0] - mx[batch_index][i][1] if mx and batch_index < len(mx) and i < len(
                    mx[batch_index]) else 0
                row = [i + 1] + LABELS[i] + volume_percentages[i][batch_index] + differences[i][batch_index]
                
                # 添加颗粒数量数据
                if particle_counts and i < len(particle_counts) and batch_index < len(particle_counts[i]):
                    row.extend(particle_counts[i][batch_index])
                else:
                    row.extend([0, 0, 0, 0, 0, 0])
                
                # 添加汇总误差
                row.append(differences_sum[i][batch_index])
                
                # 添加细度模数数据
                if mx and batch_index < len(mx) and i < len(mx[batch_index]):
                    row.extend([mx[batch_index][i][0], mx[batch_index][i][1], mx_error])
                else:
                    row.extend([0, 0, 0])
                    
                # 单个样本行不显示方差，添加空值
                row.extend(["", ""])
                writer.writerow(row)

            # 输出平均
            row = [None] * len(headers)
            row[0] = "平均"
            row[-6] = mean_absolute_differences[batch_index]  # 汇总误差的平均值位置变了
            
            # 计算颗粒数平均值
            if particle_counts:
                total_particles = [0, 0, 0, 0, 0, 0]
                for i in range(len(particle_counts)):
                    if batch_index < len(particle_counts[i]):
                        for j in range(len(total_particles)):
                            total_particles[j] += particle_counts[i][batch_index][j]
                # 将颗粒数平均值放在正确的位置
                particle_start_idx = 1 + len(gradeNames) * 3  # Sample + 标签 + 占比 + 误差 后的位置
                for j in range(len(total_particles)):
                    row[particle_start_idx + j] = total_particles[j]
            
            # 计算细度模数的平均值
            if mx and batch_index < len(mx):
                mx_calc_avg = sum(m[0] for m in mx[batch_index]) / len(mx[batch_index])
                mx_label_avg = sum(m[1] for m in mx[batch_index]) / len(mx[batch_index])
                mx_error_avg = mx_calc_avg - mx_label_avg
                row[-5] = mx_calc_avg  # 位置变了
                row[-4] = mx_label_avg
                row[-3] = mx_error_avg
            
            # 添加方差信息
            error_variance = statistics.variance(error_values) if len(error_values) > 1 else 0
            mx_error_variance = statistics.variance(mx_error_values) if len(mx_error_values) > 1 else 0
            row[-2] = error_variance  # 级配误差方差
            row[-1] = mx_error_variance  # 细度模数误差方差
            
            writer.writerow(row)

    filename1 = f"result{mixture_sample_index - 1}/Summary_{experiment_name}.csv"
    isNewFile = not os.path.exists(filename1)
    with open(filename1, mode='a', newline='') as file:
        writer = csv.writer(file)
        # Compute statistics
        max_value = max(mean_absolute_differences)
        min_value = min(mean_absolute_differences)
        mean_value = statistics.mean(mean_absolute_differences)
        std_dev_value = 0 if len(mean_absolute_differences) == 1 else statistics.stdev(mean_absolute_differences)
        median_value = statistics.median(mean_absolute_differences)
        q1_value = np.percentile(mean_absolute_differences, 25)
        q3_value = np.percentile(mean_absolute_differences, 75)
        # 计算级配误差的方差
        variance_value = 0 if len(mean_absolute_differences) == 1 else statistics.variance(mean_absolute_differences)
        try:
            mode_value = statistics.mode(list(map(lambda x: round(x), mean_absolute_differences)))
        except statistics.StatisticsError:
            mode_value = "No unique mode"

        # 计算颗粒总数
        total_particles_all_batches = [0, 0, 0, 0, 0, 0]
        if particle_counts:
            for sample_counts in particle_counts:
                for batch_counts in sample_counts:
                    for i, count in enumerate(batch_counts):
                        total_particles_all_batches[i] += count

        # 计算细度模数的统计值
        if mx:
            # 从所有批次中收集细度模数值
            mx_calc_values = []
            mx_label_values = []
            mx_error_values = []

            for batch in mx:
                for sample in batch:
                    mx_calc_values.append(sample[0])
                    mx_label_values.append(sample[1])
                    mx_error_values.append(sample[0] - sample[1])

            mx_calc_mean = statistics.mean(mx_calc_values)
            mx_label_mean = statistics.mean(mx_label_values)
            mx_error_mean = statistics.mean(mx_error_values)
            # 计算细度模数误差的方差
            mx_error_variance = statistics.variance(mx_error_values) if len(mx_error_values) > 1 else 0
        else:
            mx_calc_mean = 0
            mx_label_mean = 0
            mx_error_mean = 0
            mx_error_variance = 0

        # Write statistics to footer
        if isNewFile:
            writer.writerow(["Statistics", "Maximum Value", "Minimum Value", "Average (Mean) Value",
                             "Standard Deviation Value", "Variance Value", "Median Value", "First Quartile (Q1) Value",
                             "Third Quartile (Q3) Value", "Mode Value",
                             "颗粒总数", "细度模数(计算值)平均", "细度模数(标签值)平均", "细度模数误差平均", "细度模数误差方差"])
        writer.writerow([filename, max_value, min_value, mean_value, std_dev_value, variance_value,
                         median_value, q1_value, q3_value, mode_value,
                         sum(total_particles_all_batches),
                         mx_calc_mean, mx_label_mean, mx_error_mean, mx_error_variance])

    # # Write data
    # for i in range(len(volume_percentages)):
    #     row = [i] + LABELS[i] + volume_percentages[i] + [differences[i]]
    #     writer.writerow(row)
def doGradesRangeExperiment(grades_range,experiment_name,batchInterval):
    if calculate_type:
        volume_percentages, particle_counts = compute_volume_percentages(grades_range,batchInterval)
    else:
        volume_percentages, particle_counts, particle_passing_rates, volume_passing_rates = compute_volume_percentages(grades_range,batchInterval)

    print(volume_percentages)
    
    differences,differences_sum,mean_absolute_differences = computeDifferences(volume_percentages,LABELS,batchInterval)

    # 细度模数计算
    mx = []
    for t in range(0, batchInterval):
        mx_value = []
        for j,volume_percentage in enumerate(volume_percentages):
            n_v = volume_percentage[t] + [0]
            n_l = LABELS[j] + [0]
            mx_value.append([get_mx(n_v),get_mx(n_l)])
        mx.append(mx_value)
    
    # 计算通过率的误差
    passing_differences = None
    if not calculate_type:
        passing_differences = compute_passing_rate_differences(
            particle_passing_rates, volume_passing_rates, LABELS, batchInterval)

    if calculate_type:
        write_to_csv(LABELS, volume_percentages, differences, differences_sum, mean_absolute_differences, experiment_name, batchInterval, mx, particle_counts)
    else:
        write_to_csv_with_passing_rates(LABELS, volume_percentages, differences, differences_sum, mean_absolute_differences, 
                                       experiment_name, batchInterval, mx, particle_counts, 
                                       particle_passing_rates, volume_passing_rates, passing_differences)

    if calculate_type:
        return volume_percentages, differences, differences_sum, mean_absolute_differences
    else:
        return volume_percentages, differences, differences_sum, mean_absolute_differences, particle_passing_rates, volume_passing_rates

def write_to_csv_with_passing_rates(LABELS, volume_percentages, differences, differences_sum, mean_absolute_differences, experiment_name,
                 batchInterval, mx, particle_counts, particle_passing_rates, volume_passing_rates, passing_differences):
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"result{mixture_sample_index - 1}/output_{current_time}_{view}_{experiment_name}_B{batchInterval}_with_passing.csv"
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)

        # 定义通过率计算用的标签列表 - 从0.15到4.75
        passing_grades = [0.15, 0.3, 0.6, 1.18, 2.36, 4.75]
        
        # 解包通过率误差的数据
        (label_passing_rates, 
         particle_passing_differences, particle_passing_differences_sum, mean_particle_passing_differences,
         volume_passing_differences, volume_passing_differences_sum, mean_volume_passing_differences) = passing_differences
        
        # Write headers with passing rates
        headers = ["Sample"] + [f"{x}_标签" for x in gradeNames] \
                  + [f"{x}_占比" for x in gradeNames] \
                  + [f"{x}_误差" for x in gradeNames] \
                  + [f"{x}_颗粒数" for x in gradeNames] \
                  + [f"{x}_标签通过率" for x in passing_grades] \
                  + [f"{x}_颗粒通过率" for x in passing_grades] \
                  + [f"{x}_颗粒通过率误差" for x in passing_grades] \
                  + [f"{x}_体积通过率" for x in passing_grades] \
                  + [f"{x}_体积通过率误差" for x in passing_grades] \
                  + [f"汇总误差", "颗粒通过率汇总误差", "体积通过率汇总误差"] \
                  + ["细度模数(计算值)", "细度模数(标签值)", "细度模数误差"] \
                  + ["误差方差", "细度模数误差方差", "颗粒通过率误差方差", "体积通过率误差方差"]
        writer.writerow(headers)

        for batch_index in range(0, batchInterval):
            # 计算当前批次的方差
            error_values = []
            mx_error_values = []
            particle_passing_error_values = []
            volume_passing_error_values = []
            
            for i in range(len(volume_percentages)):
                # 收集误差数据用于计算方差
                error_values.append(differences_sum[i][batch_index])
                
                # 收集细度模数误差数据
                if mx and batch_index < len(mx) and i < len(mx[batch_index]):
                    mx_error_values.append(mx[batch_index][i][0] - mx[batch_index][i][1])
                
                # 收集通过率误差数据
                if batch_index < len(particle_passing_differences_sum[i]):
                    particle_passing_error_values.append(particle_passing_differences_sum[i][batch_index])
                
                if batch_index < len(volume_passing_differences_sum[i]):
                    volume_passing_error_values.append(volume_passing_differences_sum[i][batch_index])
                    
            for i in range(len(volume_percentages)):
                # 计算细度模数误差
                mx_error = mx[batch_index][i][0] - mx[batch_index][i][1] if mx and batch_index < len(mx) and i < len(
                    mx[batch_index]) else 0
                    
                # 基本信息
                row = [i + 1] + LABELS[i] + volume_percentages[i][batch_index] + differences[i][batch_index]
                
                # 添加颗粒数量数据
                if particle_counts and i < len(particle_counts) and batch_index < len(particle_counts[i]):
                    row.extend(particle_counts[i][batch_index])
                else:
                    row.extend([0, 0, 0, 0, 0, 0])
                
                # 添加标签通过率
                row.extend(label_passing_rates[i])
                
                # 添加颗粒通过率
                if i < len(particle_passing_rates) and batch_index < len(particle_passing_rates[i]):
                    row.extend(particle_passing_rates[i][batch_index])
                else:
                    row.extend([0, 0, 0, 0, 0, 0])
                
                # 添加颗粒通过率误差
                if i < len(particle_passing_differences) and batch_index < len(particle_passing_differences[i]):
                    row.extend(particle_passing_differences[i][batch_index])
                else:
                    row.extend([0, 0, 0, 0, 0, 0])
                
                # 添加体积通过率
                if i < len(volume_passing_rates) and batch_index < len(volume_passing_rates[i]):
                    row.extend(volume_passing_rates[i][batch_index])
                else:
                    row.extend([0, 0, 0, 0, 0, 0])
                
                # 添加体积通过率误差
                if i < len(volume_passing_differences) and batch_index < len(volume_passing_differences[i]):
                    row.extend(volume_passing_differences[i][batch_index])
                else:
                    row.extend([0, 0, 0, 0, 0, 0])
                
                # 添加汇总误差
                row.append(differences_sum[i][batch_index])
                
                # 添加通过率汇总误差
                if i < len(particle_passing_differences_sum) and batch_index < len(particle_passing_differences_sum[i]):
                    row.append(particle_passing_differences_sum[i][batch_index])
                else:
                    row.append(0)
                    
                if i < len(volume_passing_differences_sum) and batch_index < len(volume_passing_differences_sum[i]):
                    row.append(volume_passing_differences_sum[i][batch_index])
                else:
                    row.append(0)
                
                # 添加细度模数数据
                if mx and batch_index < len(mx) and i < len(mx[batch_index]):
                    row.extend([mx[batch_index][i][0], mx[batch_index][i][1], mx_error])
                else:
                    row.extend([0, 0, 0])
                    
                # 单个样本行不显示方差，添加空值
                row.extend(["", "", "", "", ""])
                writer.writerow(row)

            # 输出平均
            row = [None] * len(headers)
            row[0] = "平均"
            
            # 计算颗粒数平均值
            if particle_counts:
                total_particles = [0, 0, 0, 0, 0, 0]
                for i in range(len(particle_counts)):
                    if batch_index < len(particle_counts[i]):
                        for j in range(len(total_particles)):
                            total_particles[j] += particle_counts[i][batch_index][j]
                # 将颗粒数平均值放在正确的位置
                particle_start_idx = 1 + len(gradeNames) * 3  # Sample + 标签 + 占比 + 误差 后的位置
                for j in range(len(total_particles)):
                    row[particle_start_idx + j] = total_particles[j]
            
            # 标签通过率平均值位置
            label_passing_start_idx = particle_start_idx + len(passing_grades)
            # 不需要计算标签通过率的平均值，因为每个样本的标签通过率是不同的
            
            # 计算颗粒通过率平均值
            if particle_passing_rates:
                avg_particle_passing = [0, 0, 0, 0, 0, 0]
                count = 0
                for i in range(len(particle_passing_rates)):
                    if batch_index < len(particle_passing_rates[i]):
                        count += 1
                        for j in range(len(avg_particle_passing)):
                            avg_particle_passing[j] += particle_passing_rates[i][batch_index][j]
                
                if count > 0:
                    avg_particle_passing = [x / count for x in avg_particle_passing]
                
                # 将平均颗粒通过率放在正确位置
                particle_passing_start_idx = label_passing_start_idx + len(passing_grades)
                for j in range(len(avg_particle_passing)):
                    row[particle_passing_start_idx + j] = avg_particle_passing[j]
            
            # 计算颗粒通过率误差平均值
            if particle_passing_differences:
                avg_particle_passing_diff = [0, 0, 0, 0, 0, 0]
                count = 0
                for i in range(len(particle_passing_differences)):
                    if batch_index < len(particle_passing_differences[i]):
                        count += 1
                        for j in range(len(avg_particle_passing_diff)):
                            avg_particle_passing_diff[j] += particle_passing_differences[i][batch_index][j]
                
                if count > 0:
                    avg_particle_passing_diff = [x / count for x in avg_particle_passing_diff]
                
                # 将平均颗粒通过率误差放在正确位置
                particle_passing_diff_start_idx = particle_passing_start_idx + len(avg_particle_passing)
                for j in range(len(avg_particle_passing_diff)):
                    row[particle_passing_diff_start_idx + j] = avg_particle_passing_diff[j]
            
            # 计算体积通过率平均值
            if volume_passing_rates:
                avg_volume_passing = [0, 0, 0, 0, 0, 0]
                count = 0
                for i in range(len(volume_passing_rates)):
                    if batch_index < len(volume_passing_rates[i]):
                        count += 1
                        for j in range(len(avg_volume_passing)):
                            avg_volume_passing[j] += volume_passing_rates[i][batch_index][j]
                
                if count > 0:
                    avg_volume_passing = [x / count for x in avg_volume_passing]
                
                # 将平均体积通过率放在正确位置
                volume_passing_start_idx = particle_passing_diff_start_idx + len(avg_particle_passing_diff)
                for j in range(len(avg_volume_passing)):
                    row[volume_passing_start_idx + j] = avg_volume_passing[j]
            
            # 计算体积通过率误差平均值
            if volume_passing_differences:
                avg_volume_passing_diff = [0, 0, 0, 0, 0, 0]
                count = 0
                for i in range(len(volume_passing_differences)):
                    if batch_index < len(volume_passing_differences[i]):
                        count += 1
                        for j in range(len(avg_volume_passing_diff)):
                            avg_volume_passing_diff[j] += volume_passing_differences[i][batch_index][j]
                
                if count > 0:
                    avg_volume_passing_diff = [x / count for x in avg_volume_passing_diff]
                
                # 将平均体积通过率误差放在正确位置
                volume_passing_diff_start_idx = volume_passing_start_idx + len(avg_volume_passing)
                for j in range(len(avg_volume_passing_diff)):
                    row[volume_passing_diff_start_idx + j] = avg_volume_passing_diff[j]
            
            # 汇总误差位置
            error_idx = volume_passing_diff_start_idx + len(avg_volume_passing_diff)
            row[error_idx] = mean_absolute_differences[batch_index]
            
            # 通过率汇总误差
            row[error_idx + 1] = mean_particle_passing_differences[batch_index]
            row[error_idx + 2] = mean_volume_passing_differences[batch_index]
            
            # 计算细度模数的平均值
            mx_idx = error_idx + 3
            if mx and batch_index < len(mx):
                mx_calc_avg = sum(m[0] for m in mx[batch_index]) / len(mx[batch_index])
                mx_label_avg = sum(m[1] for m in mx[batch_index]) / len(mx[batch_index])
                mx_error_avg = mx_calc_avg - mx_label_avg
                row[mx_idx] = mx_calc_avg
                row[mx_idx + 1] = mx_label_avg
                row[mx_idx + 2] = mx_error_avg
            
            # 添加方差信息
            error_variance = statistics.variance(error_values) if len(error_values) > 1 else 0
            mx_error_variance = statistics.variance(mx_error_values) if len(mx_error_values) > 1 else 0
            particle_passing_error_variance = statistics.variance(particle_passing_error_values) if len(particle_passing_error_values) > 1 else 0
            volume_passing_error_variance = statistics.variance(volume_passing_error_values) if len(volume_passing_error_values) > 1 else 0
            
            row[-4] = error_variance  # 级配误差方差
            row[-3] = mx_error_variance  # 细度模数误差方差
            row[-2] = particle_passing_error_variance  # 颗粒通过率误差方差
            row[-1] = volume_passing_error_variance  # 体积通过率误差方差
            
            writer.writerow(row)

    # 摘要文件基本不变，添加通过率误差的统计
    filename1 = f"result{mixture_sample_index - 1}/Summary_{experiment_name}.csv"
    isNewFile = not os.path.exists(filename1)
    with open(filename1, mode='a', newline='') as file:
        writer = csv.writer(file)
        # Compute statistics
        max_value = max(mean_absolute_differences)
        min_value = min(mean_absolute_differences)
        mean_value = statistics.mean(mean_absolute_differences)
        std_dev_value = 0 if len(mean_absolute_differences) == 1 else statistics.stdev(mean_absolute_differences)
        median_value = statistics.median(mean_absolute_differences)
        q1_value = np.percentile(mean_absolute_differences, 25)
        q3_value = np.percentile(mean_absolute_differences, 75)
        # 计算级配误差的方差
        variance_value = 0 if len(mean_absolute_differences) == 1 else statistics.variance(mean_absolute_differences)
        try:
            mode_value = statistics.mode(list(map(lambda x: round(x), mean_absolute_differences)))
        except statistics.StatisticsError:
            mode_value = "No unique mode"

        # 计算颗粒总数
        total_particles_all_batches = [0, 0, 0, 0, 0, 0]
        if particle_counts:
            for sample_counts in particle_counts:
                for batch_counts in sample_counts:
                    for i, count in enumerate(batch_counts):
                        total_particles_all_batches[i] += count

        # 计算细度模数的统计值
        if mx:
            # 从所有批次中收集细度模数值
            mx_calc_values = []
            mx_label_values = []
            mx_error_values = []

            for batch in mx:
                for sample in batch:
                    mx_calc_values.append(sample[0])
                    mx_label_values.append(sample[1])
                    mx_error_values.append(sample[0] - sample[1])

            mx_calc_mean = statistics.mean(mx_calc_values)
            mx_label_mean = statistics.mean(mx_label_values)
            mx_error_mean = statistics.mean(mx_error_values)
            # 计算细度模数误差的方差
            mx_error_variance = statistics.variance(mx_error_values) if len(mx_error_values) > 1 else 0
        else:
            mx_calc_mean = 0
            mx_label_mean = 0
            mx_error_mean = 0
            mx_error_variance = 0
            
        # 计算通过率误差的统计值
        particle_passing_mean = statistics.mean(mean_particle_passing_differences) if mean_particle_passing_differences else 0
        volume_passing_mean = statistics.mean(mean_volume_passing_differences) if mean_volume_passing_differences else 0
        
        particle_passing_variance = statistics.variance(mean_particle_passing_differences) if len(mean_particle_passing_differences) > 1 else 0
        volume_passing_variance = statistics.variance(mean_volume_passing_differences) if len(mean_volume_passing_differences) > 1 else 0

        # Write statistics to footer
        if isNewFile:
            writer.writerow(["Statistics", "Maximum Value", "Minimum Value", "Average (Mean) Value",
                             "Standard Deviation Value", "Variance Value", "Median Value", "First Quartile (Q1) Value",
                             "Third Quartile (Q3) Value", "Mode Value",
                             "颗粒总数", "细度模数(计算值)平均", "细度模数(标签值)平均", "细度模数误差平均", "细度模数误差方差",
                             "颗粒通过率误差平均", "颗粒通过率误差方差", "体积通过率误差平均", "体积通过率误差方差"])
        writer.writerow([filename, max_value, min_value, mean_value, std_dev_value, variance_value,
                         median_value, q1_value, q3_value, mode_value,
                         sum(total_particles_all_batches),
                         mx_calc_mean, mx_label_mean, mx_error_mean, mx_error_variance,
                         particle_passing_mean, particle_passing_variance, volume_passing_mean, volume_passing_variance])

def compute_passing_rate_differences(particle_passing_rates, volume_passing_rates, LABELS, batchInterval):
    # 计算标签的通过率
    label_passing_rates = []
    
    for label_row in LABELS:
        # 计算标签累积通过率
        total = sum(label_row)
        passing = 0
        label_passing = []
        for val in label_row:
            passing += val
            label_passing.append(passing / total)
        label_passing_rates.append(label_passing)
    
    # 计算颗粒通过率误差
    particle_passing_differences = []
    particle_passing_differences_sum = []
    
    for i, sample_rates in enumerate(particle_passing_rates):
        sample_differences = []
        sample_differences_sum = []
        
        for batch_index in range(len(sample_rates)):
            # 计算与标签的差异
            diff = []
            for j in range(len(sample_rates[batch_index])):
                # 标签通过率 - 计算通过率
                diff.append(label_passing_rates[i][j] - sample_rates[batch_index][j])
            diff_sum = sum(abs(d) for d in diff)
            sample_differences.append(diff)
            sample_differences_sum.append(diff_sum)
        
        particle_passing_differences.append(sample_differences)
        particle_passing_differences_sum.append(sample_differences_sum)
    
    # 计算体积通过率误差
    volume_passing_differences = []
    volume_passing_differences_sum = []
    
    for i, sample_rates in enumerate(volume_passing_rates):
        sample_differences = []
        sample_differences_sum = []
        
        for batch_index in range(len(sample_rates)):
            # 计算与标签的差异
            diff = []
            for j in range(len(sample_rates[batch_index])):
                # 标签通过率 - 计算通过率
                diff.append(label_passing_rates[i][j] - sample_rates[batch_index][j])
            
            diff_sum = sum(abs(d) for d in diff)
            sample_differences.append(diff)
            sample_differences_sum.append(diff_sum)
        
        volume_passing_differences.append(sample_differences)
        volume_passing_differences_sum.append(sample_differences_sum)
    
    # 计算每个批次的平均误差
    mean_particle_passing_differences = [0] * batchInterval
    mean_volume_passing_differences = [0] * batchInterval
    
    for i in range(len(particle_passing_differences_sum)):
        for batch_index in range(min(batchInterval, len(particle_passing_differences_sum[i]))):
            mean_particle_passing_differences[batch_index] += particle_passing_differences_sum[i][batch_index]
    
    for i in range(len(volume_passing_differences_sum)):
        for batch_index in range(min(batchInterval, len(volume_passing_differences_sum[i]))):
            mean_volume_passing_differences[batch_index] += volume_passing_differences_sum[i][batch_index]
    
    # 计算平均值
    samples_count = len(particle_passing_differences_sum)
    if samples_count > 0:
        mean_particle_passing_differences = [x / samples_count for x in mean_particle_passing_differences]
        mean_volume_passing_differences = [x / samples_count for x in mean_volume_passing_differences]
    
    return (label_passing_rates, 
            particle_passing_differences, particle_passing_differences_sum, mean_particle_passing_differences,
            volume_passing_differences, volume_passing_differences_sum, mean_volume_passing_differences)

def experiment():
    # 计算分布
    # distributions=[[0, 0, 0], [3.0026, 0.8557, 290810], [6.2798, 1.6112, 152812], [11.6693, 2.8601, 121086], [22.6277, 5.0845, 55936], [39.8, 8.1722, 36366]]
    if view == "local":  
        distributions=[[15.726148501650561, 5.025908898455741, 102310], [24.532296428473334, 5.90580308492185, 53052], [73.29206511379361, 18.1987845979488, 22216], [137.64206089586784, 31.976187288998567, 18387], [268.34254052593064, 57.206654572788054, 6954], [455.65862488762764, 84.82154053305035, 5916]]
    else:
        distributions=[[0, 0, 0], [5.558337013329231, 1.736477733988356, 266954], [13.062050557909743, 3.5652616689807415, 157012], [25.478479538512886, 6.284976689925735, 116730], [50.466823358962024, 11.149710850849603, 53382], [87.94593298872343, 16.900539175831565, 35452]]
    distributions = calculate_mean_and_variance(distributions)
    print(distributions)

    
    # distributions = [[x[0],x[1]*0.5,x[2]] for x in distributions]

    # Get both intersection values and curve data
    # intersection_cdf_values, curve_data = normal5.plot_normal_distributions(distributions, None, False, True)
    intersection_cdf_values = normal5.plot_normal_distributions(distributions,None,True)
    print(intersection_cdf_values)

    # Uncomment the following line to debug and visualize the curves directly 
    # normal5.plot_normal_distributions(distributions, None, True, False)

    # 根据交叉点计算每个区间
    grades_range = gen_grades_range_by_intersection(intersection_cdf_values,distributions)
    doGradesRangeExperiment(grades_range,"交叉点计算每个区间",1)
    # for i in range(5,101,5):    
    #     doGradesRangeExperiment(grades_range,f"交叉点计算每个区间",i)
    
 

#     # 根据交叉点计算每个区间,交叉点扩展每个区间,扩展个extendStdRatio个标准差
#     extendStdRatio = 0.1
#     grades_range = gen_grades_range_by_intersection(intersection_cdf_values,distributions,extendStdRatio)
#     doGradesRangeExperiment(grades_range,fr"交叉点计算每个区间,扩展{extendStdRatio}")


#    # 根据交叉点计算每个区间,交叉点扩展每个区间,扩展个extendStdRatio个标准差
#     extendStdRatio = 0.2
#     grades_range = gen_grades_range_by_intersection(intersection_cdf_values,distributions,extendStdRatio)
#     doGradesRangeExperiment(grades_range,fr"交叉点计算每个区间,扩展{extendStdRatio}")



    # 根据交叉点计算每个区间,交叉点扩展每个区间,扩展个extendStdRatio个标准差
    # extendStdRatio = 0.4
    # grades_range = gen_grades_range_by_intersection(intersection_cdf_values,distributions,extendStdRatio)
    # doGradesRangeExperiment(grades_range,fr"交叉点计算每个区间,扩展{extendStdRatio}")


#     # 根据交叉点计算每个区间,交叉点扩展每个区间,扩展个extendStdRatio个标准差
#     extendStdRatio = 0.6
#     grades_range = gen_grades_range_by_intersection(intersection_cdf_values,distributions,extendStdRatio)
#     doGradesRangeExperiment(grades_range,fr"交叉点计算每个区间,扩展{extendStdRatio}")

#     # 根据交叉点计算每个区间,交叉点扩展每个区间,扩展个extendStdRatio个标准差
#     extendStdRatio = 0.8
#     grades_range = gen_grades_range_by_intersection(intersection_cdf_values,distributions,extendStdRatio)
#     doGradesRangeExperiment(grades_range,fr"交叉点计算每个区间,扩展{extendStdRatio}")

#     # 根据交叉点计算每个区间,交叉点扩展每个区间,扩展个extendStdRatio个标准差
#     extendStdRatio = 1.0
#     grades_range = gen_grades_range_by_intersection(intersection_cdf_values,distributions,extendStdRatio)
#     doGradesRangeExperiment(grades_range,fr"交叉点计算每个区间,扩展{extendStdRatio}")

#     # 根据交叉点计算每个区间,交叉点扩展每个区间,扩展个extendStdRatio个标准差
#     extendStdRatio = 1.5
#     grades_range = gen_grades_range_by_intersection(intersection_cdf_values,distributions,extendStdRatio)
#     doGradesRangeExperiment(grades_range,fr"交叉点计算每个区间,扩展{extendStdRatio}")

    # 根据均值的正负一个标准差计算每个区间
    # grades_range = list(map(lambda d:[d[0]-d[1],d[0]+d[1]],distributions)) #只统计均值正负一个标准差范围内的值
    # doGradesRangeExperiment(grades_range,"正负一个标准差")

    # 根据均值的正负0.5个标准差计算每个区间
    # grades_range = list(map(lambda d:[d[0]-d[1]*0.5,d[0]+d[1]*0.5],distributions)) #只统计均值正负一个标准差范围内的值
    # doGradesRangeExperiment(grades_range,"正负0.5个标准差")

#      # 根据均值的正负0.3个标准差计算每个区间
#     grades_range = list(map(lambda d:[d[0]-d[1]*0.3,d[0]+d[1]*0.3],distributions)) #只统计均值正负一个标准差范围内的值
#     doGradesRangeExperiment(grades_range,"正负0.3个标准差")   

#     # 根据均值的正负2个标准差计算每个区间
#     grades_range = list(map(lambda d:[d[0]-d[1]*2,d[0]+d[1]*2],distributions)) #只统计均值正负一个标准差范围内的值
#     doGradesRangeExperiment(grades_range,"正负2个标准差")

    
    #根据均值的正负3个标准差计算每个区间
    # grades_range = list(map(lambda d:[d[0]-d[1]*3,d[0]+d[1]*3],distributions)) #只统计均值正负一个标准差范围内的值
    # doGradesRangeExperiment(grades_range,"正负3个标准差")


    # doIntersectionImprovedExperiment(0.5)
    # doIntersectionImprovedExperiment(3)


if __name__ == '__main__':
    # #参与计算的标志
    # gradeEnabled = [1,1,1,1,1,1]
    # data_path="/Users/chuanyunxu/Documents/DDD/workspace/Work/2025/09 砂级配/ZSH_Sand_411/new_data_txt"
    # gradeNames =[0.075,0.15,0.3,0.6,1.18,2.36]
    #
    # LABELS = [[a * b for a, b in zip(row, gradeEnabled)] for row in LABELS]
    # LABELS = [[ a/sum(row) for a in row] for row in LABELS]
    #
    # volume_corrections =[2,0.8,1,1,1,1]
    # volume_corrections =[2,1,1,1,1,1]
    # volume_corrections =[1,1,1,1,1,1]
    #
    # volume_corrections = [a*b for a,b in zip(volume_corrections,gradeEnabled)]
    #
    # view = "local"
    experiment()
    # view = "global"
    # experiment()