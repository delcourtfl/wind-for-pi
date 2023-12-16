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

    async function getDataFromFirestore() {
        try {
            setLoading(true);
            const querySnapshot = await getDocs(query(refData, orderBy("fullTime")));
            const newdata = querySnapshot.docs.map((doc) => doc.data());
            console.log(newdata);
            setData(newdata);
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
                <h1>Firestore Wind4Pi</h1>
                <button className="button" onClick={() => setFetchData(!fetchData)}>Fetch Data</button>
            </div>
            <div className="containerBot">
                <div className="graph-container">
                    {loading ? (
                        <p>Loading...</p>
                    ) : (
                        <Graph data={data} />
                    )}
                </div>
                <div className="table-container">
                    {loading ? (
                        <p>Loading...</p>
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
                    <th>Timestamps</th>
                    <th>Voltages</th>
                </tr>
            </thead>
            <tbody>
                {data.map((obj, index) => (
                    <tr key={index}>
                        <td>{obj?.fullTime.toDate().toString()}</td>
                        <td>{obj?.value}</td>
                    </tr>
                ))}
            </tbody>
        </table>
    );
};

const Graph = ({ data }) => {

    React.useEffect(() => {
        // Process data to separate labels and values
        const labels = data.map(entry => entry.fullTime.seconds);
        const values = data.map(entry => entry.value);

        // Get the canvas element
        const ctx = document.getElementById('chart');

        // Create the chart using Chart.js
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Value',
                    data: values,
                    fill: false,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        // type: 'timeseries',
                        // time: {
                        //     unit: 'second' // Set the time unit as per your requirement
                        // },
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Value'
                        }
                    }
                }
            }
        });
    }, [data]); // Run effect when 'data' prop changes

    return (
        <div className="chart">
            <canvas id="chart" width="400" height="400"></canvas>
        </div>
    );
};
const root = ReactDOM.createRoot(document.getElementById("root"))
root.render(<Main />);