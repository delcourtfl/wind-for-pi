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
    const [loading, setLoading] = React.useState(false);
    const [fetchData, setFetchData] = React.useState(false);
    
    const [activeTab, setActiveTab] = React.useState(false); // State to manage active tab

    async function getDataFromFirestore() {
        try {
            setLoading(true);
            const querySnapshot = await getDocs(query(refData, orderBy("time")));
            const newdata = querySnapshot.docs.map((doc) => doc.data());

            const remappedData = [];

            newdata.forEach((dataDict) => {
                const storedTime = dataDict.time.toDate();
                for (let i = 0; i < 200; i++) {
                    const item = {};
                    const newTime = new Date(storedTime.getTime()); 
                    newTime.setMilliseconds(newTime.getMilliseconds() + i * 100);
                    item['x'] = newTime;
                    item['y'] = dataDict[i]; // cast to mV
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
            setFetchData(false);
        }
    };

    React.useEffect(() => {
        if (fetchData) {
            console.log("Fetching");
            getDataFromFirestore();
        }
    }, [fetchData]);

    return (
        <div className="fullWithLeftMargin">
            <div className="containerTop">
                <h1>Firestore Wind4Pi</h1>
                <button className="button" disabled={fetchData} onClick={() => setFetchData(true)}>Fetch Data</button>
                <button className="button" onClick={() => setActiveTab(!activeTab)}>Switch Display</button>
            </div>
            <div className="containerBot">
                <div className="graph-container" style={{ display: activeTab ? 'none' : 'block' }}>
                    {loading ? (
                        <div className="loading"></div>
                    ) : (
                        <Graph data={data} />
                    )}
                </div>
                <div className="table-container" style={{ display: activeTab ? 'block' : 'none' }}>
                    {loading ? (
                        <div className="loading"></div>
                    ) : (
                        <DataTable data={data} />
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
        // Get the canvas element
        const ctx = document.getElementById('chart');

        // Initialize the chart inside the useEffect hook
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'Value',
                    data: data,
                    fill: false,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    tension: false,
                    stepped: 0,
                    borderDash: []
                }]
            },
            options: {
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            displayFormats: {
                                hour: 'HH:mm',
                                minute: 'HH:mm',
                                second: 'HH:mm:ss'
                            }
                        }
                    },
                    y: {
                    },
                },
                animation: false,
                responsive: true,
                maintainAspectRatio: false,
                // Customize chart options as needed
            }
        });

        // Cleanup function to destroy the chart when component unmounts
        return () => {
            chart.destroy();
        };
    }, [data]); // Run effect when 'data' prop changes

    return (
        <canvas id="chart"></canvas>
    );
};
const root = ReactDOM.createRoot(document.getElementById("root"))
root.render(<Main />);