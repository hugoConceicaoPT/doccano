  <script>
  import { Pie, mixins } from 'vue-chartjs'
  const { reactiveProp } = mixins

  export default {
    extends: Pie,
    mixins: [reactiveProp],
    props: {
      chartData: {
        type: Object,
        default: () => { },
        required: true
      }
    },

    data() {
      return {
        options: {
          responsive: true,
          maintainAspectRatio: false,
          legend: {
            position: 'bottom'
          },
          tooltips: {
            enabled: true
          }
        }
      }
    },

    mounted() {
      this.renderChart(this.chartData, this.options)
    }
  }
</script>
