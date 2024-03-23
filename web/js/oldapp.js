// Import the functions you need from the SDKs you need
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-analytics.js";
import { getFirestore, collection, query, orderBy, onSnapshot, getDocs } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";

// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
    apiKey: "AIzaSyB6sRL-ZL7BLi5phz3CoiKgxEg94YvVdeY",
    authDomain: "windforpi.firebaseapp.com",
    projectId: "windforpi",
    storageBucket: "windforpi.appspot.com",
    messagingSenderId: "386673185114",
    appId: "1:386673185114:web:4eb9df27feee38ab486363",
    measurementId: "G-EPCLR8C7CM"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
const firestore = getFirestore()

var refData = collection(firestore, 'data');

const Main = () => {
    const [data, setData] = React.useState([]);
    const [fetchData, setFetchData] = React.useState(false);
    const [loading, setLoading] = React.useState(false);

    const [activeTab, setActiveTab] = React.useState(false); // State to manage active tab

    async function getDataFromFirestore() {
        try {
            setLoading(true);
            const querySnapshot = await getDocs(query(refData, orderBy("time")));
            const newdata = querySnapshot.docs.map((doc) => doc.data());
            // console.log(newdata);

            const remappedData = [];

            newdata.forEach((dataDict) => {
                const storedTime = dataDict.time.toDate();
                for (let i = 0; i < 200; i++) {
                    const item = {};
                    const newTime = new Date(storedTime.getTime()); 
                    newTime.setMilliseconds(newTime.getMilliseconds() + i * 100);
                    item['x'] = newTime;
                    item['y'] = dataDict[i]; //(Math.round(dataDict[i] * 1000) / 1000).toFixed(3); // cast to mV
                    remappedData.push(item);
                }
            });

            console.log(remappedData);
            console.log("length = " + remappedData.length);
            setData(remappedData);
        } catch (error) {
            console.error('Error fetching data:', error);
        } finally {
            setLoading(false);
        }
    };

    React.useEffect(() => {
        if (fetchData) {
            getDataFromFirestore();
        }
    }, [fetchData]);

    return (
        <div className="fullWithLeftMargin">
            <div className="containerTop">
                <div>Firestore Wind4Pi</div>
                <button className="button" onClick={() => setFetchData(!fetchData)}>Fetch Data</button>
                <button className="button" onClick={() => setActiveTab(!activeTab)}>Switch Display</button>
            </div>
            <div className="containerBot">
                <div className="content">
                    {!activeTab && (
                        <div className="graph-container">
                            {loading ? (
                                <p>Loading...</p>
                            ) : (
                                <Graph data={data} />
                            )}
                        </div>
                    )}
                    {activeTab && (
                        <div className="table-container">
                            {loading ? (
                                <p>Loading...</p>
                            ) : (
                                <DataTable data={data} />
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

const DataTable = ({ data }) => {
    return (
        <table>
            <thead>
                <tr>
                    {/* <th>Display index</th> */}
                    <th>Timestamps</th>
                    <th>Voltages</th>
                </tr>
            </thead>
            <tbody>
                {data.map((obj, index) => (
                    <tr key={index}>
                        {/* <td>{index}</td> */}
                        <td>{obj?.x.toString()}</td>
                        <td>{obj?.y}</td>
                    </tr>
                ))}
            </tbody>
        </table>
    );
};

const Graph = ({ data }) => {

    React.useEffect(() => {

        console.log("WTF FLO");
        // Process data to separate labels and values
        // const labels = data.map(entry => entry.time.toISOString());
        // const values = data.map(entry => entry.value);

        const data_filtered = data.slice(0, 10000);
        console.log(data_filtered);

        // Get the canvas element
        const ctx = document.getElementById('chart');

        const scales = {
            x: {
            //   position: 'bottom',
                type: 'time',
                // ticks: {
                //     autoSkip: true,
                //     autoSkipPadding: 5,
                //     maxRotation: 0
                // },
                time: {
                    displayFormats: {
                        hour: 'HH:mm',
                        minute: 'HH:mm',
                        second: 'HH:mm:ss'
                    }
                }
            },
            y: {
            //   position: 'right',
                // ticks: {
                //     callback: (val, index, ticks) => index === 0 || index === ticks.length - 1 ? null : val,
                // },
                // title: {
                //     display: true,
                //     // text: (ctx) => ctx.scale.axis + ' axis',
                // }
            },
          };

        const zoomOptions = {
            pan: {
                enabled: true,
                modifierKey: 'ctrl',
            },
            zoom: {
                drag: {
                    enabled: true
                },
                mode: 'xy',
            },
        };

        // Create the chart using Chart.js
        new Chart(ctx, {
            type: 'line',
            data: {
                // labels: labels,
                datasets: [{
                    label: 'Value',
                    data: data_filtered,
                    fill: false,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    tension: false,
                    stepped: 0,
                    borderDash: []
                }]
            },
            options: {
                scales: scales,
                animation: false,
                // parsing: false,
            //   plugins: {
            //     zoom: zoomOptions,
            //     title: {
            //       display: true,
            //       position: 'bottom',
            //     //   text: (ctx) => 'Zoom: ' + zoomStatus() + ', Pan: ' + panStatus()
            //     }
            //   },
            }
        });
        // new Chart(ctx, {
        //     type: 'scatter',
        //     data: {
        //         // labels: labels,
        //         datasets: [{
        //             label: 'Value',
        //             data: data,
        //             fill: false,
        //             borderColor: 'rgba(75, 192, 192, 1)',
        //             tension: false,
        //             stepped: 0,
        //             borderDash: []
        //         }]
        //     },
        //     options: {

        //         // events: ['click'],
        //         // parsing: {
        //         //     xAxisKey: 'time',
        //         //     yAxisKey: 'value'
        //         // },

        //         // Turn off animations and data parsing for performance
        //         animation: false,
        //         parsing: false,
        //         // normalized: true,

        //         // interaction: {
        //         //     mode: 'nearest',
        //         //     axis: 'x',
        //         //     intersect: false
        //         // },

        //         plugins: {
        //             decimation: {
        //                 enabled: true,
        //                 algorithm: 'min-max',
        //             },
        //             zoom: {
        //                 zoom: {
        //                     drag: {
        //                         enabled: true,
        //                         modifierKey: 'shift',
        
        //                     },
        //                     pinch: {
        //                         enabled: true
        //                     },
        //                     mode: 'x'
        //                 },
        //                 pan: {
        //                     enabled: true,
        //                     mode: 'x',
        //                     modifierKey: 'ctrl'
        //                 }
        //             }
        //         },
        //         responsive: true,
        //         maintainAspectRatio: false,
        //         scales: {
        //             x: {
        //                 title: {
        //                     display: true,
        //                     text: 'Time'
        //                 },
        //                 // type: 'time',
        //                 type: 'time',
        //                 time: {
        //                     displayFormats: {
        //                         hour: 'yyyy-MM-dd HH:mm:ss'
        //                     }
        //                 }
        //             },
        //             y: {
        //                 title: {
        //                     display: true,
        //                     text: 'Value'
        //                 }
        //             }
        //         },
        //     }
        // });
    }, [data]); // Run effect when 'data' prop changes

    return (
        <div className="chart-container">
            <canvas id="chart"></canvas>
        </div>
    );
};
const root = ReactDOM.createRoot(document.getElementById("root"))
root.render(<Main />);