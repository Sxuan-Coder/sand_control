<!-- <template>
  <div class="sand-image-results">
    <h2>Sand Particle Image Processing Results</h2>
    
    <div class="processing-controls">
      <el-button type="primary" @click="processImages" :loading="processing">
        Process Sand Images
      </el-button>
      <el-button type="primary" @click="loadResults" :disabled="processing">
        Load Results
      </el-button>
    </div>
    
    <el-tabs v-model="activeTab" @tab-click="handleTabClick">
      <el-tab-pane label="Global Images" name="global">
        <div v-if="results.global && results.global.length > 0">
          <h3>Global Sand Particle Results</h3>
          <el-table :data="results.global" stripe style="width: 100%">
            <el-table-column prop="image_path" label="Image" width="220">
              <template #default="scope">
                <div v-if="scope.row.success">
                  {{ getFilename(scope.row.image_path) }}
                </div>
                <div v-else class="error-text">
                  {{ getFilename(scope.row.image_path) }} (Failed)
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="contours_count" label="Particles" width="100">
              <template #default="scope">
                <div v-if="scope.row.success">{{ scope.row.contours_count }}</div>
                <div v-else>-</div>
              </template>
            </el-table-column>
            <el-table-column label="Distribution" min-width="350">
              <template #default="scope">
                <div v-if="scope.row.success" class="distribution-chart">
                  <el-progress 
                    v-for="(grade, index) in scope.row.grade_statistics" 
                    :key="index"
                    :percentage="Math.round(grade.percentage * 100)"
                    :color="gradeColors[index]"
                    :stroke-width="15"
                    :format="() => formatGradeLabel(index, grade.count)"
                    class="distribution-bar"
                  />
                </div>
                <div v-else class="error-text">
                  Processing failed: {{ scope.row.error }}
                </div>
              </template>
            </el-table-column>
            <el-table-column label="Actions" width="150">
              <template #default="scope">
                <div v-if="scope.row.success">
                  <el-button 
                    type="primary" 
                    size="small" 
                    @click="viewImage(scope.row.visualization_path)"
                  >
                    View
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div v-else class="no-results">
          No global image results available.
        </div>
      </el-tab-pane>
      
      <el-tab-pane label="Local Images" name="local">
        <div v-if="results.local && results.local.length > 0">
          <h3>Local Sand Particle Results</h3>
          <el-table :data="results.local" stripe style="width: 100%">
            <el-table-column prop="image_path" label="Image" width="220">
              <template #default="scope">
                <div v-if="scope.row.success">
                  {{ getFilename(scope.row.image_path) }}
                </div>
                <div v-else class="error-text">
                  {{ getFilename(scope.row.image_path) }} (Failed)
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="contours_count" label="Particles" width="100">
              <template #default="scope">
                <div v-if="scope.row.success">{{ scope.row.contours_count }}</div>
                <div v-else>-</div>
              </template>
            </el-table-column>
            <el-table-column label="Distribution" min-width="350">
              <template #default="scope">
                <div v-if="scope.row.success" class="distribution-chart">
                  <el-progress 
                    v-for="(grade, index) in scope.row.grade_statistics" 
                    :key="index"
                    :percentage="Math.round(grade.percentage * 100)"
                    :color="gradeColors[index]"
                    :stroke-width="15"
                    :format="() => formatGradeLabel(index, grade.count)"
                    class="distribution-bar"
                  />
                </div>
                <div v-else class="error-text">
                  Processing failed: {{ scope.row.error }}
                </div>
              </template>
            </el-table-column>
            <el-table-column label="Actions" width="150">
              <template #default="scope">
                <div v-if="scope.row.success">
                  <el-button 
                    type="primary" 
                    size="small" 
                    @click="viewImage(scope.row.visualization_path)"
                  >
                    View
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div v-else class="no-results">
          No local image results available.
        </div>
      </el-tab-pane>
      
      <el-tab-pane label="Summary" name="summary">
        <div class="summary-container">
          <h3>Processing Summary</h3>
          
          <el-card class="summary-card" v-if="hasSummaryData">
            <template #header>
              <div class="card-header">
                <span>Overall Statistics</span>
              </div>
            </template>
            
            <div class="summary-stats">
              <div class="stat-item">
                <span class="stat-label">Total Images Processed:</span>
                <span class="stat-value">{{ getTotalProcessedImages() }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Total Particles Detected:</span>
                <span class="stat-value">{{ getTotalParticles() }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Processing Time:</span>
                <span class="stat-value">{{ results.timestamp || 'N/A' }}</span>
              </div>
            </div>
            
            <h4>Grade Distribution</h4>
            <div class="grade-summary">
              <el-progress 
                v-for="(percent, index) in getSummaryDistribution()" 
                :key="index"
                :percentage="Math.round(percent * 100)"
                :color="gradeColors[index]"
                :stroke-width="20"
                :format="() => gradeLabels[index]"
                class="summary-distribution-bar"
              />
            </div>
          </el-card>
          
          <div v-else class="no-results">
            No summary data available. Process images first.
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
    
    <!-- Image Viewer Dialog -->
    <el-dialog
      v-model="imageDialogVisible"
      title="Particle Visualization"
      width="80%"
    >
      <img v-if="selectedImage" :src="selectedImage" class="visualization-image" />
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { processCustomImages, getProcessingResults } from '../api/sandImageApi';
import { getImageUrl } from '../api/index';

export default {
  name: 'SandImageResults',
  
  setup() {
    const activeTab = ref('global');
    const processing = ref(false);
    const results = reactive({
      global: [],
      local: [],
      timestamp: null
    });
    
    const imageDialogVisible = ref(false);
    const selectedImage = ref('');
    
    const gradeColors = [
      '#f56c6c', // red
      '#67c23a', // green
      '#409eff', // blue
      '#e6a23c', // orange
      '#909399', // gray
      '#9a40ff'  // purple
    ];
    
    const gradeLabels = [
      '0.075~0.15mm',
      '0.15~0.3mm',
      '0.3~0.6mm',
      '0.6~1.18mm',
      '1.18~2.36mm',
      '2.36~4.75mm'
    ];
    
    const hasSummaryData = computed(() => {
      return (results.global && results.global.length > 0) || 
             (results.local && results.local.length > 0);
    });
    
    // Methods    const processImages = async () => {
      try {
        processing.value = true;
        
        // Call the Python script to process images
        const response = await processCustomImages();
        
        if (response.success) {
          ElMessage.success('Images processed successfully');
          loadResults();
        } else {
          ElMessage.error('Error processing images: ' + response.error);
        }
      } catch (error) {
        console.error('Error processing images:', error);
        ElMessage.error('Error processing images: ' + error.message);
      } finally {
        processing.value = false;
      }
    };
    
    const loadResults = async () => {
      try {
        processing.value = true;
        
        // Load the results JSON file
        const response = await getProcessingResults();
        
        if (response && response.global) {
          // Update the results object
          results.global = response.global;
          results.local = response.local;
          results.timestamp = response.timestamp;
          
          ElMessage.success('Results loaded successfully');
        } else {
          ElMessage.warning('No processing results found');
        }
      } catch (error) {
        console.error('Error loading results:', error);
        ElMessage.error('Error loading results: ' + error.message);
      } finally {
        processing.value = false;
      }
    };
    
    const handleTabClick = (tab) => {
      console.log('Tab clicked:', tab.props.name);
    };      const viewImage = (imagePath) => {
      if (imagePath.startsWith('vis_')) {
        // For visualization files, use the getImageUrl function with correct endpoint
        selectedImage.value = getImageUrl(imagePath);
      } else {
        // For other images, also use getImageUrl for consistency
        selectedImage.value = getImageUrl(imagePath);
      }
      imageDialogVisible.value = true;
    };
    
    const getFilename = (path) => {
      if (!path) return 'Unknown';
      return path.split('\\').pop().split('/').pop();
    };
    
    const formatGradeLabel = (index, count) => {
      return `${gradeLabels[index]}: ${count}`;
    };
    
    const getTotalProcessedImages = () => {
      const global = results.global ? results.global.filter(r => r.success).length : 0;
      const local = results.local ? results.local.filter(r => r.success).length : 0;
      return global + local;
    };
    
    const getTotalParticles = () => {
      let total = 0;
      
      if (results.global) {
        results.global.forEach(result => {
          if (result.success && result.contours_count) {
            total += result.contours_count;
          }
        });
      }
      
      if (results.local) {
        results.local.forEach(result => {
          if (result.success && result.contours_count) {
            total += result.contours_count;
          }
        });
      }
      
      return total;
    };
    
    const getSummaryDistribution = () => {
      // Initialize counters for each grade
      const gradeCounts = [0, 0, 0, 0, 0, 0];
      let totalParticles = 0;
      
      // Process global results
      if (results.global) {
        results.global.forEach(result => {
          if (result.success && result.grade_statistics) {
            result.grade_statistics.forEach((grade, index) => {
              gradeCounts[index] += grade.count;
              totalParticles += grade.count;
            });
          }
        });
      }
      
      // Process local results
      if (results.local) {
        results.local.forEach(result => {
          if (result.success && result.grade_statistics) {
            result.grade_statistics.forEach((grade, index) => {
              gradeCounts[index] += grade.count;
              totalParticles += grade.count;
            });
          }
        });
      }
      
      // Calculate percentages
      return totalParticles > 0 
        ? gradeCounts.map(count => count / totalParticles) 
        : [0, 0, 0, 0, 0, 0];
    };
    
    return {
      activeTab,
      processing,
      results,
      imageDialogVisible,
      selectedImage,
      gradeColors,
      gradeLabels,
      hasSummaryData,
      
      processImages,
      loadResults,
      handleTabClick,
      viewImage,
      getFilename,
      formatGradeLabel,
      getTotalProcessedImages,
      getTotalParticles,
      getSummaryDistribution
    };
  }
};
</script>

<style scoped>
.sand-image-results {
  padding: 20px;
}

.processing-controls {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.no-results {
  text-align: center;
  margin: 40px 0;
  color: #909399;
  font-style: italic;
}

.error-text {
  color: #f56c6c;
}

.distribution-chart {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.distribution-bar {
  margin-bottom: 5px;
}

.summary-container {
  padding: 20px 0;
}

.summary-card {
  margin-bottom: 20px;
}

.summary-stats {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
}

.stat-label {
  font-weight: bold;
}

.summary-distribution-bar {
  margin-bottom: 10px;
  height: 30px;
}

.visualization-image {
  width: 100%;
  max-height: 80vh;
  object-fit: contain;
}
</style> -->
